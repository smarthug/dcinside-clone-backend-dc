
from rest_framework import serializers
from .models import Gallery, Post, Comment


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['id', 'slug', 'title', 'description',
                  'is_anonymous', 'allow_images', 'created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    gallery = serializers.SlugRelatedField(
        slug_field='slug', queryset=Gallery.objects.all())
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'gallery', 'title', 'content', 'author', 'author_username',
                  'nickname', 'image', 'recommend', 'views', 'created_at', 'updated_at', 'is_notice'],
        read_only_fields = ['author', 'recommend', 'views']

    def get_author_username(self, obj):
        return obj.author.username if obj.author else None

    def create(self, validated_data):
        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_username', 'nickname',
                  'content', 'parent', 'recommend', 'created_at', 'updated_at']
        read_only_fields = ['author', 'recommend']

    def get_author_username(self, obj):
        return obj.author.username if obj.author else None

    def create(self, validated_data):
        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)
