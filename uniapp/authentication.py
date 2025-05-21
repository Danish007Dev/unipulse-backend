# authentication.py , do not delete your CustomJWTAuthentication.
# ✅ You need it because you do not use Django's User model for permissions/data,
# but your request.user in views depends on getting the correct Student / Faculty / Admin object.
# Just be sure you are not accidentally relying on Django’s default User anywhere else.
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from .models import Student, Faculty, Admin

# class CustomJWTAuthentication(JWTAuthentication):
#     def get_user(self, validated_token):
#         email = validated_token.get("email")
#         user_type = validated_token.get("user_type")

#         if not email or not user_type:
#             raise AuthenticationFailed("Invalid token payload.")

#         model = {
#             "student": Student,
#             "faculty": Faculty,
#             "admin": Admin
#         }.get(user_type)

#         if not model:
#             raise AuthenticationFailed("Invalid user type.")

#         try:
#             return model.objects.get(email=email)
#         except model.DoesNotExist:
#             raise AuthenticationFailed("User not found.")

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
            raise AuthenticationFailed("Invalid user type.")

        try:
            user_obj = model.objects.get(email=email)
            return CustomUserWrapper(user_obj, user_type)
        except model.DoesNotExist:
            raise AuthenticationFailed("User not found.")



