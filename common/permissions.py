# common/permissions.py
from rest_framework.permissions import BasePermission
from accounts.models import RoleChoices  

class IsAdmin(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.ADMIN)


class IsClient(BasePermission):
    """
    Allows access only to clients.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.CLIENT)


class IsLandscaper(BasePermission):
    """
    Allows access only to landscapers.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.LANDSCAPER)


class IsWorker(BasePermission):
    """
    Allows access only to workers.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.WORKER)
