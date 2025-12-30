# permissions.py
from rest_framework.permissions import BasePermission

class IsProLandscaper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "landscaper"
            and hasattr(request.user, "subscription")
            and request.user.subscription.is_pro
        )
