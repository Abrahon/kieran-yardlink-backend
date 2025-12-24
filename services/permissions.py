from rest_framework import permissions

class IsLandscaper(permissions.BasePermission):
    """
    Allows access only to users with role 'landscaper'.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "landscaper"
