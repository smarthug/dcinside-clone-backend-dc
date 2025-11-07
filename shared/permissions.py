from rest_framework.permissions import BasePermission


class HasLevelPermission(BasePermission):
    """
    A base permission class that checks if a user has a specific level.
    Subclasses should set the `required_level` attribute.
    """
    required_level = None

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if self.required_level is None:
            # Deny access if required_level is not set on the subclass
            return False

        # Grant access if the user's level matches the required level.
        # You could also use <= for minimum level of access.
        return request.user.level == self.required_level


class IsLevel1User(HasLevelPermission):
    """
    Allows access only to users with level = 1.
    """
    required_level = 1
