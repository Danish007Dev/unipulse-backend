from django.urls import path
from feedup.views import (
    ArticleListView, GoogleAuthView, BookmarkView, 
    FeedUpRegisterView, FeedUpLoginView,
    FeedUpSendOtpView, FeedUpVerifyOtpView,
    SyncUniPulseUserView, CheckUserView, SetFeedUpPasswordView,
)

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

     # ✅ Use a single endpoint for all bookmark actions
     path("bookmarks/", BookmarkView.as_view(), name="bookmark-list-create"),
]