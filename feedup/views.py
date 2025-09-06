from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import Article, FeedUpUser, Bookmark, AiResponseBookmark, Conference, ResearchUpdate # ✅ Import Article
from .serializers import ArticleSerializer, BookmarkSerializer, FeedUpUserRegistrationSerializer, FeedUpUserLoginSerializer, AiResponseBookmarkSerializer, ConferenceSerializer, ResearchUpdateSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from .authentication import FeedUpJWTAuthentication
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from uniapp.authentication import CustomJWTAuthentication
from uniapp.permissions import IsStudent, IsFaculty, IsAdmin
from .utils import generate_questions_for_article, get_ai_response
import logging

app_logger = logging.getLogger('feedup')

class CheckUserView(APIView):
    """Checks if a FeedUpUser exists with the given email."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = FeedUpUser.objects.filter(email__iexact=email).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)


class SyncUniPulseUserView(APIView):
    """
    Called after a successful UniPulse (student/faculty/admin) login.
    Ensures a FeedUpUser is created for SSO.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsStudent | IsFaculty | IsAdmin]

    def post(self, request):
        request_user = request.user

        # ✅ Extract profile email from Student/Faculty/Admin
        if hasattr(request_user, 'profile'):
            email = request_user.profile.email
            user, created = FeedUpUser.objects.get_or_create(email=email)
        else:
            return Response({
                "status": "error",
                "message": "Invalid user for FeedUp sync.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Optional: attach `created` info or other checks
        requires_password_setup = created or not user.password

        return Response({
            "status": "success",
            "message": f"User {user.email} synced with FeedUp.",
            "requires_password_setup": requires_password_setup,
        }, status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "ID token required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)

            email = idinfo["email"]
            google_id = idinfo["sub"]
            name = idinfo.get("name", "")

            user, _ = FeedUpUser.objects.get_or_create(
                google_id=google_id,
                defaults={"email": email, "name": name},
            )

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "email": user.email,
                    "name": user.name,
                }
            })
            
        except ValueError:
            return Response({"error": "Invalid ID token"}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.pagination import PageNumberPagination
class ArticleListPagination(PageNumberPagination):
    page_size = 10

class ArticleListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = ArticleListPagination

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            self._paginator = self.pagination_class()
        return self._paginator

    def get(self, request):
        # ✅ FIX: Fetch directly from the final Article table.
        # This table ONLY contains processed articles, so the previous
        # filtering logic was incorrect and unnecessary.
        queryset = Article.objects.all().order_by("-published_at")

        paginated_queryset = self.paginator.paginate_queryset(queryset, request, view=self)
        serializer = ArticleSerializer(paginated_queryset, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class BookmarkView(APIView):
    """
    Handle fetching, adding, and removing bookmarks for the authenticated user.
    """
    authentication_classes = [FeedUpJWTAuthentication]  # Use custom auth class
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user= request.user  
        bookmarks = user.bookmarks.all()
        articles = [bookmark.article for bookmark in bookmarks]
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        article_id = request.data.get('article_id')
        if not article_id:
            return Response({"error": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)
           
        try:
            # ✅ Query the final Article table directly.
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)
           
    
        user = request.user  
           
        bookmark, created = Bookmark.objects.get_or_create(user=user, article=article)
       
        if created:
            return Response({"status": "bookmarked"}, status=status.HTTP_201_CREATED)
        else:
            bookmark.delete()
            return Response({"status": "unbookmarked"}, status=status.HTTP_200_OK)


        
class FeedUpRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FeedUpUserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Here you would typically send an OTP for email verification
            # For now, we'll just return success.
            return Response({"message": "User registered successfully. Please verify your email."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedUpLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FeedUpUserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = FeedUpUser.objects.get(email=email)
        except FeedUpUser.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.password or not check_password(password, user.password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # If credentials are valid, generate tokens
        refresh = RefreshToken()
        refresh['email'] = user.email
        # We add a specific role to distinguish from uniapp users
        refresh['user_type'] = 'feedup_user' 

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from .models import FeedUpUser, OTPVerification
from .serializers import FeedUpUserLoginSerializer # We will use this later


class FeedUpSendOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        OTPVerification.objects.filter(email=email).delete() # Invalidate old OTPs
        otp_code = OTPVerification.generate_otp()
        OTPVerification.objects.create(email=email, otp=otp_code)

        # In a real app, you would use a service like SendGrid to email the OTP.
        # For development, we print it to the console.
        print(f"✅ OTP for {email}: {otp_code}")

        return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)

class FeedUpVerifyOtpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = OTPVerification.objects.get(email=email, otp=otp, expires_at__gt=timezone.now())
        except OTPVerification.DoesNotExist:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        is_new_user = not FeedUpUser.objects.filter(email=email).exists()
        
        if not is_new_user:
            # If the user exists, they should have been directed to the password login screen.
            # This path indicates a logic error in the frontend flow, but we handle it gracefully.
            verification.delete() # Still consume the OTP
            return Response({
                "message": "User already exists. Please log in with your password.",
                "is_new_user": False,
            }, status=status.HTTP_400_BAD_REQUEST) # Use 400 to indicate a bad request flow

        # For new users, proceed to generate a registration token
        verification.delete() # OTP is used, so delete it
        temp_token = AccessToken()
        temp_token.set_exp(lifetime=timedelta(minutes=10))
        temp_token['email'] = email
        temp_token['scope'] = 'register' # Custom claim
        return Response({
            "message": "OTP verified. Please create a password.",
            "is_new_user": True,
            "verification_token": str(temp_token)
        }, status=status.HTTP_200_OK)

class FeedUpRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        token = request.data.get('token')

        if not all([email, password, token]):
            return Response({"error": "Email, password, and token are required"}, status=status.HTTP_400_BAD_REQUEST)

        try: # Validate the temporary token from the OTP step
            decoded_token = AccessToken(token)
            if decoded_token['scope'] != 'register' or decoded_token['email'] != email:
                raise Exception()
        except Exception:
            return Response({"error": "Invalid or expired verification token"}, status=status.HTTP_401_UNAUTHORIZED)

        if FeedUpUser.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = FeedUpUser.objects.create(
            email=email,
            name=email.split('@')[0],
            password=make_password(password)
        )

        # Generate JWT tokens to log the new user in
        refresh = RefreshToken()
        refresh['email'] = user.email
        refresh['user_type'] = 'feedup_user'

        return Response({
            "message": "User registered and logged in successfully.",
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class SetFeedUpPasswordView(APIView):
    """
    Allows a UniPulse user (student/faculty) to set a password for their
    FeedUp account using their existing valid JWT.
    """
    authentication_classes = [FeedUpJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password or len(password) < 8:
            return Response({"error": "Password must be at least 8 characters"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user.password = make_password(password)
        user.save()
        
        return Response({"message": "Password set successfully"}, status=status.HTTP_200_OK)

class AskAiView(APIView):
    """
    Handles AI-related queries for articles.
    - POST without a 'query' generates initial questions.
    - POST with a 'query' gets a specific answer.
    """
    authentication_classes = [FeedUpJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        query = request.data.get('query')

        if not article_id:
            return Response({"error": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

        if query:
            # Action: Answer a user's query
            try:
                answer = get_ai_response(article, query)
                app_logger.info(f"User {request.user.email} asked '{query}' for article {article_id}")
                return Response({"answer": answer}, status=status.HTTP_200_OK)
            except Exception as e:
                app_logger.error(f"Error getting AI response for article {article_id}: {e}")
                return Response({"error": "Failed to get AI response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Action: Generate initial questions
            try:
                questions = generate_questions_for_article(article)
                app_logger.info(f"Generated questions for article {article_id} for user {request.user.email}")
                return Response({"questions": questions}, status=status.HTTP_200_OK)
            except Exception as e:
                app_logger.error(f"Error generating questions for article {article_id}: {e}")
                return Response({"error": "Failed to generate questions"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework import generics

class AiResponseBookmarkListView(generics.ListAPIView):
    """
    Provides a list of all AI response bookmarks for the authenticated user.
    """
    serializer_class = AiResponseBookmarkSerializer
    authentication_classes = [FeedUpJWTAuthentication, CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AiResponseBookmark.objects.filter(user=self.request.user)


class AiResponseBookmarkToggleView(APIView):
    """
    Creates or deletes an AI response bookmark.
    """
    authentication_classes = [FeedUpJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        question = request.data.get('question')
        answer = request.data.get('answer')

        if not all([article_id, question, answer]):
            return Response(
                {"error": "article_id, question, and answer are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

        # Try to get the bookmark
        bookmark, created = AiResponseBookmark.objects.get_or_create(
            user=request.user,
            original_article=article,
            question=question,
            defaults={'answer': answer}
        )

        if created:
            # The bookmark was just created
            serializer = AiResponseBookmarkSerializer(bookmark)
            return Response({"status": "bookmarked", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            # The bookmark already existed, so delete it
            bookmark.delete()
            return Response({"status": "bookmark_removed"}, status=status.HTTP_204_NO_CONTENT)

from rest_framework.pagination import PageNumberPagination
from .models import Conference, ResearchUpdate
from .serializers import ConferenceSerializer, ResearchUpdateSerializer
from django.utils import timezone
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from datetime import date

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConferenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Conference.objects.all()  # Add this line
    serializer_class = ConferenceSerializer
    authentication_classes = [FeedUpJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Conference.objects.all()
        
        # Get query parameters
        show_past = self.request.query_params.get('show_past', 'false').lower() == 'true'
        search = self.request.query_params.get('search', '').strip()
        location = self.request.query_params.get('location', '').strip()
        topic = self.request.query_params.get('topic', '').strip()
        
        # Filter by past/future
        today = date.today()
        if not show_past:
            queryset = queryset.filter(start_date__gte=today)
        
        # Search filter (title, description, location)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search) |
                Q(topics__icontains=search)
            )
        
        # Location filter
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Topic filter
        if topic:
            queryset = queryset.filter(topics__icontains=topic)
        
        # Order by start date
        return queryset.order_by('start_date')

class ResearchUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResearchUpdate.objects.all()  # Add this line
    serializer_class = ResearchUpdateSerializer
    authentication_classes = [FeedUpJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ResearchUpdate.objects.all()
        
        # Get query parameters
        search = self.request.query_params.get('search', '').strip()
        category = self.request.query_params.get('category', '').strip()
        institution = self.request.query_params.get('institution', '').strip()
        recent_days = self.request.query_params.get('recent_days')
        
        # Search filter (title, summary, authors)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(authors__icontains=search)
            )
        
        # Category filter
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Institution filter
        if institution:
            queryset = queryset.filter(institution__icontains=institution)
        
        # Recent filter
        if recent_days:
            try:
                days = int(recent_days)
                cutoff_date = timezone.now().date() - timezone.timedelta(days=days)
                queryset = queryset.filter(publication_date__gte=cutoff_date)
            except ValueError:
                pass
        
        # Order by publication date (newest first)
        return queryset.order_by('-publication_date')
