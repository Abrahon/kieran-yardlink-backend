# common/permissions.py
from rest_framework.permissions import BasePermission
from accounts.models import RoleChoices  

# common/permissions.py
from rest_framework.permissions import BasePermission
from accounts.models import RoleChoices
from profiles.models import LandscaperProfilies
from rest_framework.permissions import BasePermission
from accounts.enums import RoleChoices
from subscriptions.utils import get_user_plan

from rest_framework.permissions import BasePermission
from accounts.enums import RoleChoices


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == RoleChoices.ADMIN
        )


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == RoleChoices.CLIENT
        )


class IsLandscaper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == RoleChoices.LANDSCAPER
        )






from subscriptions.enums import SubscriptionStatus
from subscriptions.models import Subscription

class IsProLandscaper(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.role != RoleChoices.LANDSCAPER:
            return False

        return Subscription.objects.filter(
            user=user,
            is_active=True,
            plan__name__iexact="pro",
            status__in=[
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ]
        ).exists()


class IsBasicLandscaper(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.role != RoleChoices.LANDSCAPER:
            return False

        return getattr(user, "plan_type", None) == "Basic"


class IsWorker(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == RoleChoices.WORKER
        )