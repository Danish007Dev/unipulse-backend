from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import FeedUpUser

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
        
 