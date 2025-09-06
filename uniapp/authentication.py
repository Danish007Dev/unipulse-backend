from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Student, Faculty, Admin

class CustomUserWrapper:
    def __init__(self, user_obj, user_type):
        self.profile = user_obj
        self.user_type = user_type
        self.email = user_obj.email
        self.is_authenticated = True  # this makes DRF happy

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        email = validated_token.get("email")
        user_type = validated_token.get("user_type")

        if not email or not user_type:
            raise AuthenticationFailed("Invalid token payload.")

        model = {
            "student": Student,
            "faculty": Faculty,
            "admin": Admin
        }.get(user_type)

        if not model:
            # raise AuthenticationFailed("Invalid user type.")
            return None  # Allow unauthenticated access for non-existent user types
            # ✅ FIX: If the user_type is not one this authenticator handles,
            # fail gracefully by returning None. This allows other authenticators
            # in the chain i.e. bookmarkview's  authentication_classes = [CustomJWTAuthentication, FeedUpJWTAuthentication] to attempt to validate the token.
        try:
            user_obj = model.objects.get(email=email)
            return CustomUserWrapper(user_obj, user_type)
        except model.DoesNotExist:
            raise AuthenticationFailed("User not found.")



