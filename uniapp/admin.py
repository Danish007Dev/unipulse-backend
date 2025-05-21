import nested_admin
from django.contrib import admin
from .models import (
    Department, Course, Semester, Subject,
    Student, Faculty, Admin as AdminUser,
    OTPVerification, Post, SavedPost
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
    list_display = ("email", "department")
    search_fields = ("email",)

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