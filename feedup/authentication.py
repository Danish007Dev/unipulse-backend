from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import FeedUpUser
import logging
class FeedUpJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class for FeedUpUser that looks up users by email.
    """
    def get_user(self, validated_token):
        """
        Overrides the default user retrieval method to use the 'email' claim.
        """
        try:
            email = validated_token.get('email')
            if email is None:
                # This token is not for us or is malformed.
                return None

            # Find the user in the FeedUpUser table using the email.
            return FeedUpUser.objects.get(email=email)

        except FeedUpUser.DoesNotExist:
            # This is a critical failure: the token is valid but the user is gone.
            raise AuthenticationFailed('User not found for the given token.', code='user_not_found')
       
 

# logger = logging.getLogger('feedup')

# class FeedUpJWTAuthentication(JWTAuthentication):
#     """
#     Custom authentication class for FeedUpUser that looks up users by email.
#     """
#     def get_user(self, validated_token):
#         """
#         Overrides the default user retrieval method to use the 'email' claim.
#         """
#         try:
#             user_id = validated_token.get('user_id')
#             email = validated_token.get('email')
#             user_type = validated_token.get('user_type')
            
#             # If this is a standard JWT token with a user_id claim
#             if user_id is not None:
#                 return super().get_user(validated_token)
                
#             # If this is a FeedUp token with email claim
#             if email is not None:
#                 try:
#                     return FeedUpUser.objects.get(email=email)
#                 except FeedUpUser.DoesNotExist:
#                     raise AuthenticationFailed('User not found for the given token.', code='user_not_found')
                    
#             # If we can't determine the user, return None to let other auth classes try
#             return None

#         except Exception as e:
#             # Log the exception for debugging
#             print(f"Authentication error: {str(e)}")
#             return None  # Let other authentication classes try

#     def authenticate(self, request):
#         try:
#             result = super().authenticate(request)
#             if result is None:
#                 logger.debug(f"JWT Authentication failed for request: {request.path}")
#                 return None
            
#             user, token = result
#             logger.info(f"JWT Authentication successful for user: {user.email if hasattr(user, 'email') else 'unknown'}")
#             return user, token
#         except Exception as e:
#             logger.error(f"Error during JWT authentication: {str(e)}")
#             return None

