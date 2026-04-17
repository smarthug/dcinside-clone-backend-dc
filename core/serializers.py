
from rest_framework import serializers
from .models import Gallery, Post, Comment


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['id', 'slug', 'title', 'description', 'is_anonymous',
                  'allow_images', 'allow_comments', 'permission_read',
                  'permission_write', 'permission_admin', 'permission_per_post',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    gallery = serializers.SlugRelatedField(
        slug_field='slug', queryset=Gallery.objects.all())
    author_username = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'gallery', 'title', 'content', 'author_username', 'is_author',
                  'nickname', 'image', 'recommend', 'views', 'created_at', 'updated_at', 'is_notice', 'external_link']
        read_only_fields = ['recommend', 'views']

    def get_author_username(self, obj):
        return obj.author.username if obj.author else None

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False

    def create(self, validated_data):
        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)


class PostListSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'author_username', 'is_author',
                  'nickname', 'created_at', 'updated_at', 'is_notice', 'external_link']

    def get_author_username(self, obj):
        return obj.author.username if obj.author else None

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author_username', 'is_author', 'nickname',
                  'content', 'parent', 'recommend', 'created_at', 'updated_at']
        read_only_fields = ['recommend']

    def get_author_username(self, obj):
        return obj.author.username if obj.author else None

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False

    def create(self, validated_data):
        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)
