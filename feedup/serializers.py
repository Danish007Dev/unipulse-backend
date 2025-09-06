from .models import ArticleStaging, FeedUpUser, Bookmark, Article , AiResponseBookmark, Conference, ResearchUpdate
from rest_framework import serializers
from django.utils import timezone
from datetime import date

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


class AiResponseBookmarkSerializer(serializers.ModelSerializer):
    """
    Serializer for the AiResponseBookmark model.
    Includes a nested serializer for the original article to provide context.
    """
    # Use a lean version of the ArticleSerializer to avoid sending too much data
    original_article = ArticleSerializer(read_only=True)

    class Meta:
        model = AiResponseBookmark
        fields = ['id', 'question', 'answer', 'created_at', 'original_article']


class ConferenceSerializer(serializers.ModelSerializer):
    """Serializer for the Conference model."""
    days_until = serializers.SerializerMethodField()
    status_text = serializers.SerializerMethodField()
    deadline_text = serializers.SerializerMethodField()
    
    class Meta:
        model = Conference
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date', 'location', 
            'website_url', 'deadline_submission', 'deadline_notification', 
            'topics', 'days_until', 'status_text', 'deadline_text'
        ]
    
    def get_days_until(self, obj):
        today = date.today()
        return (obj.start_date - today).days
    
    def get_status_text(self, obj):
        days_until = self.get_days_until(obj)
        if days_until > 0:
            return f'In {days_until} days'
        elif days_until == 0:
            return 'Happening now'
        else:
            return 'Ended'
    
    def get_deadline_text(self, obj):
        if not obj.deadline_submission:
            return 'No deadline info'
        
        today = date.today()
        if obj.deadline_submission < today:
            return 'Deadline passed'
        else:
            days_left = (obj.deadline_submission - today).days
            return f'Submit in {days_left} days'

class ResearchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for the ResearchUpdate model."""
    days_since_publication = serializers.SerializerMethodField()
    recency_text = serializers.SerializerMethodField()
    
    class Meta:
        model = ResearchUpdate
        fields = [
            'id', 'title', 'summary', 'publication_date', 'url', 'source', 
            'authors', 'institution', 'category', 'days_since_publication', 
            'recency_text'
        ]
    
    def get_days_since_publication(self, obj):
        today = date.today()
        return (today - obj.publication_date).days
    
    def get_recency_text(self, obj):
        days_since = self.get_days_since_publication(obj)
        if days_since == 0:
            return 'Published today'
        elif days_since == 1:
            return 'Published yesterday'
        else:
            return f'Published {days_since} days ago'