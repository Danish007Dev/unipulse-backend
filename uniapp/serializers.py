from rest_framework import serializers
from .models import Course, Semester, Department

class OTPRequestSerializer(serializers.Serializer):
    user_type = serializers.ChoiceField(choices=["student", "faculty", "admin"])
    email = serializers.EmailField()
    enrollment_number = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    user_type = serializers.ChoiceField(choices=[("student", "student"), ("faculty", "faculty"), ("admin", "admin")])

# serializers.py

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth.models import User

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # The default validation checks the token's signature and expiration.
        data = super().validate(attrs)
        
        # Decode the refresh token to access its claims.
        refresh = RefreshToken(attrs['refresh'])
        
        user_id = refresh.get('user_id')
        email = refresh.get('email')
        user_type = refresh.get('user_type')

        # --- THIS IS THE FIX ---
        # Find the user associated with the token. If they don't exist or are
        # inactive, the token is invalid.
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise InvalidToken('User not found for the given token.')

        # Create a new access token for the *correct* user.
        new_access_token = AccessToken.for_user(user)
        
        # Re-inject the custom claims into the new access token.
        new_access_token['email'] = email
        new_access_token['user_type'] = user_type
        
        data['access'] = str(new_access_token)

        return data


from .models import Post, SavedPost

from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    content=serializers.CharField(required=False, allow_blank=True)
    # Urls-only fields for uploading to supabase storage (used during POST)
    document_url = serializers.URLField(write_only=True , required=False, allow_null=True)
    image_url = serializers.URLField(write_only=True, required=False, allow_null=True)
    # add urls fields to fetch document and image from supabase storage (used during GET)  
      # Read-only URLs (return to frontend)
    document = serializers.CharField(read_only=True)
    image = serializers.CharField(read_only=True)
    
    is_saved = serializers.SerializerMethodField()
  
    class Meta:
        model = Post
        fields = '__all__' 
        read_only_fields = ['faculty', 'created_at'] # 👈 Prevent frontend from sending iT

    # add methods below,to GET document and image from supabase storage urls


    def create(self, validated_data):
        print("✅ Clean validated_data before create:", validated_data)
        # Pop explicitly to avoid duplication error
        document = validated_data.pop('document_url', None)
        image = validated_data.pop('image_url', None)
       

        # Create the post instance
        instance = Post.objects.create(
            document=document,
            image=image,
            **validated_data
        )
        return instance
    
    def get_is_saved(self, obj):
        saved_ids = self.context.get('saved_ids', set())
        return obj.id in saved_ids
    
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']    

class SavedPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = SavedPost
        fields = '__all__'
        read_only_fields = ['student', 'saved_at']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'department']

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'name', 'course']

