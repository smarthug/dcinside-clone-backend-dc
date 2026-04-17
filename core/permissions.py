
from rest_framework.permissions import SAFE_METHODS

from core.models import Gallery, Post
from shared.permissions import IsLevel1User


class IsAuthorOrReadOnly(IsLevel1User):

    def has_permission(self, request, view):
        # Allow read-only methods (filtering is done in queryset)
        if request.method in SAFE_METHODS:
            return True

        if super().has_permission(request, view):
            return True

        gallery_slug = request.query_params.get(
            'gallery', request.data.get('gallery'))

        if not gallery_slug:
            return False

        _p = Gallery.objects.filter(slug=gallery_slug).only(
            'permission_write').first()

        if not _p:
            return False

        return request.user.is_authenticated and _p.permission_write >= request.user.level

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        if request.user.level == 1 or request.user.is_superuser:
            return True

        if getattr(obj, 'author', None) is not None and obj.author == request.user:
            return True

        gallery = getattr(obj, 'gallery', None)
        if not gallery:
            return False

        return gallery.permission_admin >= request.user.level


class IsCommentAuthorOrReadOnly(IsLevel1User):

    def has_permission(self, request, view):
        # Allow read-only methods (filtering is done in queryset)
        if request.method in SAFE_METHODS:
            return True

        if super().has_permission(request, view):
            return True

        post_id = request.query_params.get('post', request.data.get('post'))

        if not post_id:
            return False

        _p = Post.objects.select_related('gallery').filter(id=post_id).only(
            'gallery__permission_read').first()

        if not _p:
            return False

        return request.user.is_authenticated and _p.gallery.permission_read >= request.user.level

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        if request.user.level == 1 or request.user.is_superuser:
            return True

        if getattr(obj, 'author', None) is not None and obj.author == request.user:
            return True

        post = getattr(obj, 'post', None)
        gallery = getattr(post, 'gallery', None) if post else None
        if not gallery:
            return False

        return gallery.permission_admin >= request.user.level
