from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from .models import ArticleStaging, FeedUpUser, Article, Bookmark
from .utils import summarize_articles, ingest_articles
from django_object_actions import DjangoObjectActions, action
from django import forms


class ArticleStagingAdminForm(forms.ModelForm):
    class Meta:
        model = ArticleStaging
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        processed = cleaned_data.get('processed')
        summary = cleaned_data.get('summary')
        
        if processed and not summary:
            raise forms.ValidationError(
                "Cannot mark article as processed: A summary is required."
            )
        return cleaned_data


@admin.register(ArticleStaging)
class ArticleStagingAdmin(DjangoObjectActions, admin.ModelAdmin):
    form = ArticleStagingAdminForm
    change_actions = ['fetch_latest_articles', 'run_ai_summarization']
    list_display = (
        "title", "source_name", "approved", "summarized", 
        "processed", "short_summary_preview", "fetched_at",  # changed from published_at to fetched_at
    )
    list_filter = ("approved", "processed", "source_name")
    search_fields = ("title", "summary")
    readonly_fields = ("formatted_raw_content", "source_url", "published_at")
    ordering = ("-published_at",)
    date_hierarchy = "published_at"
    list_per_page = 25
    
    # Custom template for changelist
    change_list_template = 'admin/feedup/articlestaging/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch-articles/', self.admin_site.admin_view(self.fetch_articles_view), name='feedup_articlestaging_fetch_articles'),
            path('summarize-articles/', self.admin_site.admin_view(self.summarize_articles_view), name='feedup_articlestaging_summarize_articles'),
            path('process-articles/', self.admin_site.admin_view(self.process_articles_view), name='feedup_articlestaging_process_articles'),
        ]
        return custom_urls + urls

    def fetch_articles_view(self, request):
        count, errors = ingest_articles()
        msg = f"✅ Imported {count} article(s)."
        if errors:
            msg += f" ❌ {len(errors)} failed → {', '.join(errors[:3])}..."
        self.message_user(request, msg, level=messages.INFO)
        return HttpResponseRedirect(reverse('admin:feedup_articlestaging_changelist'))

    def summarize_articles_view(self, request):
        articles = ArticleStaging.objects.filter(approved=True)
        
        success_count = 0
        skipped_count = 0
        failed = []
        
        for article in articles:
            # Skip articles that already have summaries
            if article.summary:
                skipped_count += 1
                continue
                
            ok, err = summarize_articles(article)
            if ok:
                success_count += 1
            else:
                failed.append(article.title)
        
        msg = f"✅ Summarized {success_count} article(s)."
        if skipped_count:
            msg += f" ⏭️ Skipped {skipped_count} (already summarized)."
        if failed:
            msg += f" ❌ Failed: {', '.join(failed[:3])}..."
        self.message_user(request, msg)
        return HttpResponseRedirect(reverse('admin:feedup_articlestaging_changelist'))

    def process_articles_view(self, request):
        from django.core.management import call_command
        try:
            call_command('process_articles')
            self.message_user(request, "Successfully processed approved articles to Article table.")
        except Exception as e:
            self.message_user(request, f"Error processing articles: {e}", level=messages.ERROR)
        return HttpResponseRedirect(reverse('admin:feedup_articlestaging_changelist'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_object_action_permission'] = True
        # Add custom URLs to template context
        extra_context['fetch_articles_url'] = reverse('admin:feedup_articlestaging_fetch_articles')
        extra_context['summarize_articles_url'] = reverse('admin:feedup_articlestaging_summarize_articles')
        extra_context['process_articles_url'] = reverse('admin:feedup_articlestaging_process_articles')
        return super().changelist_view(request, extra_context)

    @action(label="📰 Fetch latest articles")
    def fetch_latest_articles(self, request, obj=None):
        count, errors = ingest_articles()
        msg = f"✅ Imported {count} article(s)."
        if errors:
            msg += f" ❌ {len(errors)} failed → {', '.join(errors[:3])}..."
        self.message_user(request, msg, level=messages.INFO)

    @action(label="🧠 Summarize articles")
    def run_ai_summarization(self, request, obj=None):
        articles = [obj] if obj else ArticleStaging.objects.filter(approved=True)
        
        success_count = 0
        skipped_count = 0
        failed = []
        
        for article in articles:
            if not article.approved:
                continue
            
            # Skip articles that already have summaries
            if article.summary:
                skipped_count += 1
                continue
                
            ok, err = summarize_articles(article)
            if ok:
                success_count += 1
            else:
                failed.append(article.title)
        
        msg = f"✅ Summarized {success_count} article(s)."
        if skipped_count:
            msg += f" ⏭️ Skipped {skipped_count} (already summarized)."
        if failed:
            msg += f" ❌ Failed: {', '.join(failed[:3])}..."
        self.message_user(request, msg)

    actions = [
        "mark_approved",
        "mark_unapproved",
        "mark_processed",
        "mark_unprocessed",  # Add this new action
        "clear_summary",
    ]

    fieldsets = (
        ("Metadata", {"fields": ("title", "source_url", "source_name", "published_at")}),
        ("Content & Tags", {"fields": ("formatted_raw_content", "summary", "prompts", "tag_suggestions")}),
        ("Status", {"fields": ("approved", "processed")}),
    )

    def short_summary_preview(self, obj):
        return (obj.summary[:75] + "...") if obj.summary else "-"
    short_summary_preview.short_description = "TL;DR"

    def formatted_raw_content(self, obj):
        if not obj.raw_content:
            return "-"
        return mark_safe(
            f"<div style='white-space:pre-wrap;max-height:300px;overflow:auto;"
            f"border:1px solid #ccc;padding:10px;font-size:13px;'>{obj.raw_content}</div>"
        )
    formatted_raw_content.short_description = "Raw Article Content"

    def mark_approved(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} article(s) marked as approved.")
    mark_approved.short_description = "✅ Approve selected articles"

    def mark_unapproved(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} article(s) marked as unapproved.")
    mark_unapproved.short_description = "🚫 Unapprove selected articles"

    def mark_processed(self, request, queryset):
        success_count = 0
        failed_count = 0
        
        for article in queryset:
            if not article.summary:
                failed_count += 1
                continue
                
            article.processed = True
            article.save()
            success_count += 1
        
        if success_count:
            self.message_user(request, f"✅ {success_count} article(s) marked as processed.")
        
        if failed_count:
            self.message_user(
                request, 
                f"❌ {failed_count} article(s) couldn't be processed: Missing summaries.", 
                level=messages.WARNING
            )

    mark_processed.short_description = "✅ Mark selected articles as processed"

    def mark_unprocessed(self, request, queryset):
        updated = queryset.update(processed=False)
        self.message_user(request, f"🔄 {updated} article(s) marked as unprocessed.")
    mark_unprocessed.short_description = "🔄 Mark selected articles as unprocessed"

    def clear_summary(self, request, queryset):
        updated = queryset.update(summary="", prompts="")
        self.message_user(request, f"🧹 Cleared summaries for {updated} article(s).")
    clear_summary.short_description = "🧹 Clear summary & prompts"

    def save_model(self, request, obj, form, change):
        # Check if user is trying to mark an article as processed
        if 'processed' in form.changed_data and obj.processed:
            # If summary is empty, prevent processing and show warning
            if not obj.summary:
                obj.processed = False
                messages.warning(request, f"Cannot mark '{obj.title}' as processed: Article must have a summary first.")
        
        super().save_model(request, obj, form, change)

    # Add this method
    def summarized(self, obj):
        """Return True if the article has a summary, False otherwise."""
        return bool(obj.summary)
    summarized.short_description = "Summarized"
    summarized.boolean = True  # This makes it display as an icon

    def fetched_at(self, obj):
        return obj.published_at
    fetched_at.short_description = "Fetched At"  # This changes the column header
    fetched_at.admin_order_field = 'published_at'  # This ensures sorting works correctly

class BookmarkInline(admin.TabularInline):
    model = Bookmark
    extra = 0
    readonly_fields = ('article',)
    can_delete = False  # you can make it True if you want inline delete

@admin.register(FeedUpUser)
class FeedUpUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'google_id', 'created_at')
    search_fields = ('email', 'name')
    readonly_fields = ('created_at', 'google_id')
    inlines = [BookmarkInline]

@admin.register(Article)
class ArticlesAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_name', 'published_at', 'summary')
    search_fields = ('title', 'source_name')
    readonly_fields = ('published_at',)

    
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'article')
    search_fields = ('user', 'article__title')

    def has_add_permission(self, request):
        return False