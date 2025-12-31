from rest_framework.permissions import BasePermission
from subscriptions.models import Subscription  # import from subscription app

class IsProLandscaper(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.role != "landscaper":
            return False

        active_subs = Subscription.objects.filter(
            user=request.user,
            is_active=True,
            plan__name__icontains="Pro"
        )
        return active_subs.exists()

