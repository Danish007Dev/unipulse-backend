import random
import datetime
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import CustomTokenRefreshSerializer
from .models import (
    Student, Faculty, Admin, OTPVerification, Course,
    Semester, Department, Post, SavedPost
)
from .serializers import (
    OTPRequestSerializer, OTPVerifySerializer, CourseSerializer,
    SemesterSerializer, PostSerializer, DepartmentSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
#from .tokens import generate_custom_tokens
from .permissions import IsStudent, IsFaculty, IsAdmin
from .authentication import CustomJWTAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError, NotFound
from .utils import get_user_by_type_and_details


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_type = serializer.validated_data["user_type"]
            email = serializer.validated_data["email"]
            enrollment_number = serializer.validated_data.get("enrollment_number")
            department = serializer.validated_data.get("department")

            try:
                user = get_user_by_type_and_details(
                    user_type=user_type,
                    email=email,
                    enrollment_number=enrollment_number,
                    department_name=department
                )
            except (ValidationError, NotFound) as e:
                return Response({"error": str(e.detail)}, status=e.status_code)

            otp = random.randint(100000, 999999)
            OTPVerification.objects.update_or_create(
                email=email,
                defaults={"otp": otp, "created_at": timezone.now()}
            )

            send_mail(
                "Your UniPulse OTP Code",
                f"Your OTP is {otp}. It is valid for 5 minutes.",
                "no-reply@unipulse.com",
                [email],
                fail_silently=False,
            )

            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]
            user_type = serializer.validated_data["user_type"]

            otp_entry = OTPVerification.objects.filter(email=email, otp=str(otp)).first()

            if not otp_entry or otp_entry.is_expired():
                return Response({"error": "Invalid or expired OTP"}, status=400)

            # OTP is valid, delete it
            otp_entry.delete()

            # Get actual user from your model
            user_model = {
                "student": Student,
                "faculty": Faculty,
                "admin": Admin
            }.get(user_type)

            if not user_model:
                return Response({"error": "Invalid user type"}, status=400)

            profile = user_model.objects.filter(email=email).first()
            if not profile:
                return Response({"error": "User not found"}, status=404)

            # 🔐 Create Django User if not already present
            django_user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email}
            )

            # 🔑 Create refresh and access tokens
            refresh = RefreshToken.for_user(django_user)
            refresh["email"] = email
            refresh["user_type"] = user_type

            access = refresh.access_token
            access["email"] = email
            access["user_type"] = user_type

            return Response({
                "message": "OTP verified successfully",
                "access_token": str(access),
                "refresh_token": str(refresh)
            }, status=200)

        return Response(serializer.errors, status=400)

    
class CustomTokenRefreshView(TokenRefreshView):# ask if its okay to make this endpoint public?
    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer

from rest_framework.pagination import PageNumberPagination
class StudentPostPagination(PageNumberPagination):
    page_size = 10


class StudentPostListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user.profile
        saved_only = request.query_params.get('saved') == 'true' # optional filtering for saved posts (via ?saved=true),to on saved post screen

        if saved_only:
            post_queryset = Post.objects.filter(
                id__in=SavedPost.objects.filter(student=student).values_list('post_id', flat=True)
            )
        else:
            post_queryset = Post.objects.filter(
                course=student.course,
                semester=student.semester
            )

        post_queryset = post_queryset.order_by('-created_at')

        paginator = StudentPostPagination()
        page = paginator.paginate_queryset(post_queryset, request)

        # Pre-fetch saved IDs to pass into serializer context
        saved_ids = set(SavedPost.objects.filter(student=student).values_list('post_id', flat=True))

        serializer = PostSerializer(
            page,
            many=True,
            context={'request': request, 'saved_ids': saved_ids}
        )

        return paginator.get_paginated_response(serializer.data)    
    

class ToggleSavePostView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        student = request.user.profile
        post_id = request.data.get('post_id')

        if not post_id:
            return Response({"error": "Post ID is required"}, status=400)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        saved_post, created = SavedPost.objects.get_or_create(student=student, post=post)

        if not created:
            saved_post.delete()
            return Response({"message": "Post unsaved"}, status=200)

        return Response({"message": "Post saved"})


        
class FacultyPostListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        faculty = request.user.profile
        course_id = request.query_params.get('course_id')
        semester_id = request.query_params.get('semester_id')

        posts = Post.objects.filter(faculty=faculty)

        if course_id and course_id.lower() not in ['none', 'null']:
            posts = posts.filter(course__id=course_id)

        if semester_id and semester_id.lower() not in ['none', 'null']:
            posts = posts.filter(semester__id=semester_id)

        posts = posts.order_by('-created_at')

        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        paginated_posts = paginator.paginate_queryset(posts, request)

        serializer = PostSerializer(paginated_posts, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
class FacultyPostCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsFaculty]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        print(f"POST DATA: {request.POST}")
        print("FILES RECEIVED:", request.FILES)
        faculty = request.user.profile
        data = request.data.copy()
        data['department'] = faculty.department.id

        serializer = PostSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save(faculty=faculty, department=faculty.department)
            return Response(PostSerializer(post, context={'request': request}).data, status=201)
        return Response(serializer.errors, status=400)


class FacultyPostDeleteView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsFaculty]

    def delete(self, request, post_id):
        faculty = request.user.profile
        try:
            post = Post.objects.get(id=post_id, faculty=faculty)
            post.delete()  # ✅ signal handles file cleanup
            return Response({"detail": "Post deleted."}, status=200)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found or unauthorized."}, status=404)



class FacultyCoursesAPIView(APIView):#for faculty dashboard ,This lets the frontend fetch all courses assigned to the faculty. 
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        faculty = request.user.profile
        courses = faculty.courses.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

class SemestersByCourseAPIView(APIView):#for faculty dashboard 
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        semesters = Semester.objects.filter(course_id=course_id)
        if not semesters.exists():# check if the course exists to avoid unnecessary 500 errors
         return Response({'detail': 'No semesters found for this course.'}, status=404)
        serializer = SemesterSerializer(semesters, many=True)
        return Response(serializer.data)
    
class DepartmentListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)    
# if returning hundreds of entries,add pagination later — but for now, this gives a clean list.    


class FacultyMajorsAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        """Get research majors for the authenticated faculty member."""
        try:
            faculty = request.user.profile  # This uses your custom authentication
            majors = [major.category for major in faculty.majors.all()]
            return Response({'majors': majors})
        except Exception as e:
            return Response({'majors': [], 'error': str(e)}, status=500)