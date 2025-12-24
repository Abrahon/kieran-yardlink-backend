from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import LandscaperProfileSerializer
from subscriptions.models import Subscription

class CompleteLandscaperProfileView(generics.CreateAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Enforce role
        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can complete this profile.")

        # Check subscription
        subscription = Subscription.objects.filter(
            user=user,
            status="active"
        ).first()

        plan_name = subscription.plan.name.lower() if subscription else "basic"

        # If image is provided but user is not Pro, block it
        profile_image = serializer.validated_data.get("profile")
        if profile_image and "pro" not in plan_name:
            raise PermissionDenied("Only Pro subscription users can upload a profile image.")

        # Save profile
        serializer.save()
