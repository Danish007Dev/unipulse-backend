# from rest_framework.permissions import BasePermission
# from uniapp.authentication import CustomUserWrapper # Adjust import if needed
# from .models import FeedUpUser

# class IsAuthenticatedFromAnyApp(BasePermission):
#     """
#     Allows access to any authenticated user, whether they are a
#     FeedUpUser or a wrapped user from the main UniApp (Student/Faculty).
#     """
#     message = "Authentication credentials were not provided or are invalid."

#     def has_permission(self, request, view):
#         # Check if the user object exists and has the 'is_authenticated' flag.
#         # This works for both Django's standard user and the CustomUserWrapper.
#         return request.user and request.user.is_authenticated
