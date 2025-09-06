from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView 

from feedup.views import (
    ArticleListView, GoogleAuthView, BookmarkView, 
    FeedUpRegisterView, FeedUpLoginView,
    FeedUpSendOtpView, FeedUpVerifyOtpView,
    SyncUniPulseUserView, CheckUserView, SetFeedUpPasswordView, AskAiView, 
    AiResponseBookmarkListView, AiResponseBookmarkToggleView,
    # Add our new viewsets
    ConferenceViewSet, ResearchUpdateViewSet
)

# Create a router for our viewsets
router = DefaultRouter()
router.register(r'conferences', ConferenceViewSet, basename='conferences')
router.register(r'research', ResearchUpdateViewSet, basename='research')

urlpatterns = [
     path("articles/", ArticleListView.as_view(), name="article-list"),
     path("google-login/", GoogleAuthView.as_view(), name="google-login"),
     
     # SSO Endpoint
     path("auth/sync-unipulse-user/", SyncUniPulseUserView.as_view(), name="sync-unipulse-user"),

     # New Email Auth Flow
     path("auth/check-user/", CheckUserView.as_view(), name="feedup-check-user"), # 👈 Add new path
     path("auth/send-otp/", FeedUpSendOtpView.as_view(), name="feedup-send-otp"),
     path("auth/verify-otp/", FeedUpVerifyOtpView.as_view(), name="feedup-verify-otp"),
     path("auth/register/", FeedUpRegisterView.as_view(), name="feedup-register"),
     path("auth/login/", FeedUpLoginView.as_view(), name="feedup-login"),
     path("auth/set-password/", SetFeedUpPasswordView.as_view(), name="feedup-set-password"),

     # Dedicated token refresh endpoint for FeedUp users
     path("auth/token/refresh/", TokenRefreshView.as_view(), name="feedup-token-refresh"),

     # ✅ Use a single endpoint for all bookmark actions
     path("bookmarks/", BookmarkView.as_view(), name="bookmark-list-create"),

    # Add the new URL pattern for the Ask AI feature
    path("ask-ai/", AskAiView.as_view(), name="ask-ai"),

    # Add the new URL patterns for AI bookmarks
    path("ai-bookmarks/", AiResponseBookmarkListView.as_view(), name="ai-bookmark-list"),
    path("ai-bookmarks/toggle/", AiResponseBookmarkToggleView.as_view(), name="ai-bookmark-toggle"),
    
    # Include the router URLs
    path('', include(router.urls)),
]