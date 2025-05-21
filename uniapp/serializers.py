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

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = RefreshToken(attrs['refresh'])
        
        # Read the claims from the refresh token
        email = refresh.get('email')
        user_type = refresh.get('user_type')

        # Inject into new access token
        access = AccessToken.for_user(self.context['request'].user)
        access['email'] = email
        access['user_type'] = user_type

        data['access'] = str(access)
        return data

# # post_serializer
# from .models import Post

# class PostSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Post
#         fields = '__all__'

# # saved_post_serializer
# from .models import SavedPost

# class SavedPostSerializer(serializers.ModelSerializer):
#     post = PostSerializer(read_only=True)

#     class Meta:
#         model = SavedPost
#         fields = ['id', 'post', 'saved_at']


from .models import Post, SavedPost

# class PostSerializer(serializers.ModelSerializer):
#     course_name = serializers.CharField(source='course.name', read_only=True)
#     semester_name = serializers.CharField(source='semester.name', read_only=True)
#     class Meta:
#         model = Post
#         fields = '__all__'
#         read_only_fields = ['faculty', 'created_at']

from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    content=serializers.CharField(required=False, allow_blank=True)

    # Read-only URL fields (used during GET)
    document = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
     # Upload-only fields (used during POST)
    document_upload = serializers.FileField(write_only=True, required=False, allow_null=True)
    image_upload = serializers.ImageField(write_only=True, required=False, allow_null=True)

    is_saved = serializers.SerializerMethodField()
  
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['faculty', 'created_at'] # 👈 Prevent frontend from sending iT

    def get_document(self, obj):
        request = self.context.get('request')
        if obj.document and hasattr(obj.document, 'url'):
            return request.build_absolute_uri(obj.document.url)
        return None

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def create(self, validated_data):
        # Map upload fields to model fields
        document = validated_data.pop('document_upload', None)
        image = validated_data.pop('image_upload', None)
        
        # Create the post instance
        instance = Post.objects.create(
            document=document,
            image=image,
            **validated_data
        )
        return instance
    
    # def create(self, validated_data):
    #     # Pop upload-only fields and map them to model fields
    #     validated_data['document'] = validated_data.pop('document_upload', None)
    #     validated_data['image'] = validated_data.pop('image_upload', None)
    #     return super().create(validated_data)
    
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

