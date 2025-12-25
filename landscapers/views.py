from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import LandscaperProfileSerializer
from subscriptions.models import Subscription

from rest_framework.exceptions import ValidationError
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from .models import LandscaperProfile
from .serializers import LandscaperProfileSerializer

class CompleteLandscaperProfileView(generics.CreateAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Enforce role
        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can complete this profile.")

        # Check if profile already exists
        if hasattr(user, "landscaper_profile"):
            raise ValidationError("Profile already exists for this user.")

        # Check subscription
        subscription = Subscription.objects.filter(user=user, status="active").first()
        plan_name = subscription.plan.name.lower() if subscription else "basic"

        # If image is provided but user is not Pro, block it
        profile_image = serializer.validated_data.get("profile")
        if profile_image and "pro" not in plan_name:
            raise PermissionDenied("Only Pro subscription users can upload a profile image.")

        # Save profile
        serializer.save()
    


class GetLandscaperProfileView(generics.RetrieveAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.landscaper_profile  # related_name from OneToOneField
        except LandscaperProfile.DoesNotExist:
            raise NotFound("Landscaper profile not found for this user.")

