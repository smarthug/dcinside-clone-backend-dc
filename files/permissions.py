
from rest_framework.permissions import SAFE_METHODS

from core.models import Gallery
from shared.permissions import IsLevel1User


class IsAuthorOrReadOnly(IsLevel1User):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if super().has_permission(request, view):
            return True

        gallery_slug = request.data.get('gallery', None)

        if not gallery_slug:
            return False

        _p = Gallery.objects.filter(slug=gallery_slug).only(
            'permission_write').first()

        if not _p:
            return False

        return request.user.is_authenticated and _p.permission_write >= request.user.level

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            gallery = getattr(obj, 'gallery', None)
            if gallery:
                user_level = getattr(request.user, 'level', 100)
                if gallery.permission_read >= user_level:
                    return True
            return False

        if not request.user.is_authenticated:
            return False

        if request.user.level == 1 or (getattr(obj, 'author', None) is not None and obj.author == request.user):
            return True

        gallery = getattr(obj, 'gallery', None)
        if not gallery:
            return False

        return gallery.permission_admin >= request.user.level

