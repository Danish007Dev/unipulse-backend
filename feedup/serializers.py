from .models import ArticleStaging, FeedUpUser, Bookmark, Article # ✅ Use ArticleStaging
from rest_framework import serializers

class YourFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedUpUser
        fields = ['id', 'email', 'name', 'google_id', 'created_at']
        read_only_fields = ['id', 'created_at']

class ArticleStagingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleStaging
        fields = [
            "id",
            "title",
            "summary",        
            "raw_content",
            "source_url",
            "source_name",
            "published_at",
            "tag_suggestions",  
            "processed",
            "approved",
            # "ai_generated",
            "prompts",
        ]

# ✅ This serializer should use the final Article model
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "summary",
            "source_url",
            "source_name",
            "published_at",
        ]

class BookmarkSerializer(serializers.ModelSerializer):
    # Nest the article details within the bookmark
    article = ArticleSerializer(read_only=True)

    class Meta:
        model = Bookmark
        fields = ['id', 'article', 'created_at']


# --- New Serializers for FeedUp Email/Password Auth ---

class FeedUpUserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedUpUser
        fields = ['id', 'email', 'name', 'password', 'google_id', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = FeedUpUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data.get('name', ''),
            password=validated_data['password']
        )
        return user

class FeedUpUserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)