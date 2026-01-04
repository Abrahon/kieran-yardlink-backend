from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import LandscaperProfileSerializer
from subscriptions.models import Subscription

from rest_framework.exceptions import ValidationError
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from .models import LandscaperProfile
from .serializers import LandscaperProfileSerializer

from rest_framework import generics, permissions
from django.db.models import Q
from bookings.models import ServiceBooking
from .models import LandscaperProfile

from bookings.models import BookingStatus

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



# for client search
class LandscaperFind(generics.ListAPIView):
    """
    Search and filter landscapers.
    Optional query params:
    - name: partial match on landscaper name
    - city: filter by city
    - service: filter by service ID
    - previous_work: 'true' or 'false' to show only landscapers the client worked with
    """
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]  # client must be logged in

    def get_queryset(self):
        queryset = LandscaperProfile.objects.all()
        user = self.request.user
        params = self.request.query_params

        # Filter by name
        name = params.get("name")
        if name:
            queryset = queryset.filter(full_name__icontains=name)

        # Filter by city
        city = params.get("city")
        if city:
            queryset = queryset.filter(city__icontains=city)

        # Filter by service ID
        service_id = params.get("service")
        if service_id:
            queryset = queryset.filter(services__id=service_id)

        # Filter by previous work
        prev_work = params.get("previous_work")
        if prev_work and prev_work.lower() == "true":
            # Get landscapers client has worked with
            worked_landscaper_ids = ServiceBooking.objects.filter(
                client=user,
                status=BookingStatus.COMPLETED
            ).values_list("landscaper_id", flat=True)
            queryset = queryset.filter(id__in=worked_landscaper_ids)

        return queryset.distinct()
