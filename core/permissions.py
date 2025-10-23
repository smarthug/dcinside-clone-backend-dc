
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not getattr(obj, 'author', None):
            return request.user and request.user.is_staff
        return obj.author == request.user or request.user.is_staff
