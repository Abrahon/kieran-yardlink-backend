# common/permissions.py
from rest_framework.permissions import BasePermission
from accounts.models import RoleChoices  

# common/permissions.py
from rest_framework.permissions import BasePermission
from accounts.models import RoleChoices
from profiles.models import LandscaperProfilies  


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.ADMIN)


class IsClient(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.CLIENT)


class IsLandscaper(BasePermission):
    """
    Allows access only to landscapers (Basic + Pro)
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.LANDSCAPER)


# NEW — PRO LANDSCAPER ONLY
class IsProLandscaper(BasePermission):
    """
    Allows access only to PRO landscapers
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user.is_authenticated and user.role == RoleChoices.LANDSCAPER):
            return False

        return LandscaperProfilies.objects.filter(
            user=user,
            plan=LandscaperProfilies.PRO
        ).exists()


#  OPTIONAL — BASIC LANDSCAPER ONLY
class IsBasicLandscaper(BasePermission):
    """
    Allows access only to BASIC landscapers
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user.is_authenticated and user.role == RoleChoices.LANDSCAPER):
            return False

        return LandscaperProfilies.objects.filter(
            user=user,
            plan=LandscaperProfilies.BASIC
        ).exists()


class IsWorker(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == RoleChoices.WORKER)
