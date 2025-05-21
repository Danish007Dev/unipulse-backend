from rest_framework.permissions import BasePermission
from .views import Student 

# class IsStudent(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and request.user.role == "student"
#         #return request.auth.get('user_type') == 'student'

# class IsFaculty(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and request.user.role == "faculty"

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and request.user.role == "admin"


from .models import Student, Faculty, Admin

# class IsStudent(BasePermission):
#     def has_permission(self, request, view):
#         return isinstance(request.user, Student)

# class IsFaculty(BasePermission):
#     def has_permission(self, request, view):
#         return isinstance(request.user, Faculty)

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return isinstance(request.user, Admin)
    
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
    