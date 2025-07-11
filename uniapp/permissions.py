from rest_framework.permissions import BasePermission
from .views import Student 
from .models import Student, Faculty, Admin


    
# ✅ This is safe, explicit, and works perfectly with your custom authentication setup.

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "user_type") and request.user.user_type == "student"

class IsFaculty(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "user_type") and request.user.user_type == "faculty"

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "user_type") and request.user.user_type == "admin"
    