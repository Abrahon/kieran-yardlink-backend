from rest_framework.permissions import BasePermission
from subscriptions.models import Subscription  # import from subscription app
from rest_framework.permissions import BasePermission
from subscriptions.models import Subscription

class IsProLandscaper(BasePermission):
    """
    Allows only Pro landscapers
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != "landscaper":
            return False
        return Subscription.objects.filter(
            user=request.user,
            is_active=True,
            plan__name__icontains="Pro"
        ).exists()


class IsBasicLandscaper(BasePermission):
    """
    Allows only Basic landscapers
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != "landscaper":
            return False
        return Subscription.objects.filter(
            user=request.user,
            is_active=True,
            plan__name__icontains="Basic"
        ).exists()

class IsProOrBasicLandscaper(BasePermission):
    """
    Wrapper permission: allow if either Pro or Basic
    """
    def has_permission(self, request, view):
        return IsProLandscaper().has_permission(request, view) or \
               IsBasicLandscaper().has_permission(request, view)

# from rest_framework.permissions import BasePermission
# from .models import BusinessEmployee

# class HasCalendarAccess(BasePermission):
#     def has_permission(self, request, view):
#         try:
#             employee = BusinessEmployee.objects.get(
#                 user=request.user,
#                 is_active=True
#             )
#             return employee.permissions.can_access_calendar
#         except:
#             return False