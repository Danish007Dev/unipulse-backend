"""
URL configuration for unipulse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
from uniapp.views import VerifyOTPView, RequestOTPView, CustomTokenRefreshView, StudentPostListView, ToggleSavePostView,FacultyPostListView, FacultyPostCreateView, FacultyCoursesAPIView, SemestersByCourseAPIView, FacultyPostDeleteView, DepartmentListView

from rest_framework_simplejwt.views import TokenBlacklistView


def home_redirect(request):
    return redirect('admin/')   # Change this to your preferred route

urlpatterns = [
   path("views/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
   path("token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
   path("admin/", admin.site.urls),
   path('admin/', include('nested_admin.urls')),
   path("views/request-otp/", RequestOTPView.as_view(), name="request-otp"),
   path("views/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
   
   path('views/student/posts/', StudentPostListView.as_view(), name='student-posts'),
   path('views/student/posts/save/', ToggleSavePostView.as_view(), name='save-post'),
   # path('views/student/save-post/', SavePostView.as_view(), name='save-post'),
#    path('views/student/saved-posts/', SavedPostsListView.as_view(), name='saved-posts'),
   path('views/faculty/posts/', FacultyPostListView.as_view(), name='faculty-post-list'),
   path('views/faculty/posts/create/', FacultyPostCreateView.as_view(), name='faculty-post-create'),
   path('views/faculty/courses/', FacultyCoursesAPIView.as_view(), name='faculty-courses'),
   path('views/course/<int:course_id>/semesters/', SemestersByCourseAPIView.as_view(), name='semesters-by-course'),
   path('views/faculty/posts/<int:post_id>/', FacultyPostDeleteView.as_view(), name='delete-post'),
   path('views/departments/', DepartmentListView.as_view(), name='department-list'), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# This does two things:
# Saves files under project_root/media/posts/docs/filename.pdf
# Serves them at http://localhost:8000/media/posts/docs/filename.pdf in development