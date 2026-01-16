
from rest_framework.permissions import SAFE_METHODS

from core.models import Gallery
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

        gallery_slug = request.query_params.get(
            'gallery', request.data.get('gallery'))

        if not gallery_slug:
            return False

        _p = Gallery.objects.filter(slug=gallery_slug).only(
            'permission_admin').first()

        if not _p:
            return False

        if not getattr(obj, 'author', None):
            return request.user.is_authenticated and (request.user.level == 1 or _p.permission_admin >= request.user.level)

        return request.user.is_authenticated and (obj.author == request.user or request.user.level == 1 or _p.permission_admin >= request.user.level)
