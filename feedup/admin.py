from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from .models import ArticleStaging, FeedUpUser, Article, Bookmark
from .utils import summarize_articles, ingest_articles
from django_object_actions import DjangoObjectActions, action


@admin.register(ArticleStaging)
class ArticleStagingAdmin(DjangoObjectActions, admin.ModelAdmin):
    change_actions = ['fetch_latest_articles', 'run_ai_summarization']
    list_display = (
        "title", "source_name", "approved", "processed",
        "short_summary_preview", "published_at",
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
        failed = []
        
        for article in articles:
            if not article.approved:
                continue
            ok, err = summarize_articles(article)
            if ok:
                success_count += 1
            else:
                failed.append(article.title)
        
        msg = f"✅ Summarized {success_count} article(s)."
        if failed:
            msg += f" ❌ Failed: {', '.join(failed[:3])}..."
        self.message_user(request, msg)
        return HttpResponseRedirect(reverse('admin:feedup_articlestaging_changelist'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_object_action_permission'] = True
        # Add custom URLs to template context
        extra_context['fetch_articles_url'] = reverse('admin:feedup_articlestaging_fetch_articles')
        extra_context['summarize_articles_url'] = reverse('admin:feedup_articlestaging_summarize_articles')
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
        failed = []
        
        for article in articles:
            if not article.approved:
                continue
            ok, err = summarize_articles(article)
            if ok:
                success_count += 1
            else:
                failed.append(article.title)
        
        msg = f"✅ Summarized {success_count} article(s)."
        if failed:
            msg += f" ❌ Failed: {', '.join(failed[:3])}..."
        self.message_user(request, msg)

    actions = [
        "mark_approved",
        "mark_unapproved",
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

    
    