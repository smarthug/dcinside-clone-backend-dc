
from django.contrib import admin
from .models import Gallery, Post, Comment, PostVote, CommentVote

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'title', 'is_anonymous', 'allow_images', 'created_at')
    search_fields = ('slug', 'title')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'gallery', 'title', 'author', 'nickname', 'recommend', 'views', 'created_at')
    search_fields = ('title', 'content', 'nickname')
    list_filter = ('gallery',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'nickname', 'recommend', 'created_at')
    search_fields = ('content', 'nickname')

@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'value')

@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'user', 'value')
