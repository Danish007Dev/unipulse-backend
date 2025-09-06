import nested_admin
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    Department, Course, Semester, Subject,
    Student, Faculty, Admin as AdminUser,
    OTPVerification, Post, SavedPost, ResearchMajor
)

# === Nested Inlines ===

class SubjectInline(nested_admin.NestedTabularInline):
    model = Subject
    extra = 1

class SemesterInline(nested_admin.NestedTabularInline):
    model = Semester
    inlines = [SubjectInline]
    extra = 1

class CourseInline(nested_admin.NestedTabularInline):
    model = Course
    inlines = [SemesterInline]
    extra = 1

@admin.register(Department)
class DepartmentAdmin(nested_admin.NestedModelAdmin):
    inlines = [CourseInline]
    list_display = ("name",)
    search_fields = ("name",)

# === Regular Admins ===

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("enrollment_number", "email", "course", "department")
    search_fields = ("enrollment_number", "email")

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'department', 'get_majors']
    list_filter = ['department', 'majors']
    search_fields = ['name', 'email']
    filter_horizontal = ['courses', 'majors']  # Nice UI for many-to-many
    
    def get_majors(self, obj):
        """Display faculty's research majors"""
        majors = obj.majors.all()
        if majors:
            return ", ".join([major.name for major in majors])
        return "No majors assigned"
    get_majors.short_description = "Research Majors"

@admin.register(AdminUser)
class AdminAdmin(admin.ModelAdmin):
    list_display = ("email", "department")
    search_fields = ("email",)

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("email", "otp", "created_at")
    search_fields = ("email",)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("faculty", "course", "semester", "subject", "created_at")
    search_fields = ("content",)
    list_filter = ("department", "course", "semester")

@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ("student", "post", "saved_at")
    search_fields = ("student__email", "post__content")
    list_filter = ("student",)

@admin.register(ResearchMajor)
class ResearchMajorAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description', 'faculty_count', 'action_buttons']
    list_filter = ['category']
    search_fields = ['name', 'category', 'description']
    ordering = ['category', 'name']
    
    # Enable bulk actions and default delete
    actions = ['delete_selected_majors', 'duplicate_selected_majors', 'delete_selected']
    
    # IMPORTANT: Allow deletion
    def has_delete_permission(self, request, obj=None):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def action_buttons(self, obj):
        """Custom action buttons for each research major"""
        edit_url = reverse('admin:uniapp_researchmajor_change', args=[obj.id])
        delete_url = reverse('admin:uniapp_researchmajor_delete', args=[obj.id])

        faculty_count = obj.faculty_members.count()
        delete_disabled = faculty_count > 0

        if delete_disabled:
            onclick = "alert('Cannot delete: assigned to faculty'); return false;"
            href = "#"
            button_class = "button disabled"
        else:
            onclick = "return confirm('Delete this major?');"
            href = delete_url
            button_class = "button"

        delete_button = (
            f'<a class="{button_class}" href="{href}" onclick="{onclick}">Delete</a>'
        )

        return format_html(
            '<a class="button" href="{}">Edit</a> {}',
            edit_url, delete_button
        )
    action_buttons.short_description = "Actions"
    
    def delete_model(self, request, obj):
        """Override delete to check for faculty assignments"""
        faculty_count = obj.faculty_members.count()
        
        if faculty_count > 0:
            self.message_user(
                request,
                f"Cannot delete '{obj.name}' because it is assigned to {faculty_count} faculty member(s). "
                "Please reassign faculty first.",
                level=messages.ERROR
            )
            # Return without deleting - Django will handle the redirect
            return
        
        # Safe to delete
        super().delete_model(request, obj)
        self.message_user(
            request,
            f"Successfully deleted research major '{obj.name}'.",
            level=messages.SUCCESS
        )
    
    def faculty_count(self, obj):
        """Show how many faculty members have this major"""
        count = obj.faculty_members.count()
        if count > 0:
            url = reverse('admin:uniapp_faculty_changelist') + f'?majors__id__exact={obj.id}'
            return format_html('<a href="{}">{} faculty</a>', url, count)
        return '0 faculty'
    faculty_count.short_description = "Faculty Members"
    
    def delete_selected_majors(self, request, queryset):
        """Custom bulk delete action with confirmation"""
        faculty_with_majors = []
        
        # Check if any selected majors are assigned to faculty
        for major in queryset:
            faculty_count = major.faculty_members.count()
            if faculty_count > 0:
                faculty_with_majors.append(f"{major.name} ({faculty_count} faculty)")
        
        if faculty_with_majors:
            self.message_user(
                request,
                f"Warning: The following majors are assigned to faculty members: {', '.join(faculty_with_majors)}. "
                "Please reassign faculty before deleting these majors.",
                level=messages.WARNING
            )
            return HttpResponseRedirect(request.get_full_path())
        
        # Safe to delete
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f"Successfully deleted {count} research major(s).",
            level=messages.SUCCESS
        )
    
    delete_selected_majors.short_description = "Delete selected research majors (with safety check)"
    
    def duplicate_selected_majors(self, request, queryset):
        """Duplicate selected research majors"""
        duplicated = 0
        
        for major in queryset:
            # Create a copy with modified name
            try:
                new_major = ResearchMajor.objects.create(
                    name=f"{major.name} (Copy)",
                    category=major.category,
                    description=f"Copy of: {major.description}" if major.description else "Copy"
                )
                duplicated += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error duplicating {major.name}: {str(e)}",
                    level=messages.ERROR
                )
        
        if duplicated > 0:
            self.message_user(
                request,
                f"Successfully duplicated {duplicated} research major(s).",
                level=messages.SUCCESS
            )
    
    duplicate_selected_majors.short_description = "Duplicate selected research majors"
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on conditions"""
        readonly_fields = []
        
        # If major is assigned to faculty, make category readonly to prevent breaking assignments
        if obj and obj.faculty_members.exists():
            readonly_fields.append('category')
            
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Override save to add custom logic"""
        if change:
            # Editing existing major
            try:
                old_obj = ResearchMajor.objects.get(pk=obj.pk)
                if old_obj.category != obj.category and obj.faculty_members.exists():
                    self.message_user(
                        request,
                        f"Warning: Changing category for '{obj.name}' may affect research paper filtering "
                        f"for {obj.faculty_members.count()} faculty member(s).",
                        level=messages.WARNING
                    )
            except ResearchMajor.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)
        
        if not change:
            # Creating new major
            self.message_user(
                request,
                f"Successfully created research major '{obj.name}'. "
                "You can now assign it to faculty members.",
                level=messages.SUCCESS
            )

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)  # Add custom CSS if needed
        }
        js = ('admin/js/custom_admin.js',)  # Add custom JS if needed