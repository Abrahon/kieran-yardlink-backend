from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import LandscaperProfileSerializer
from subscriptions.models import Subscription

from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from .models import LandscaperProfile
from django.db.models import Q
from bookings.models import ServiceBooking
from .models import LandscaperProfile
# landscapers/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WorkingHours, LandscaperProfile, DAYS_OF_WEEK
from .serializers import WorkingHoursSerializer
from bookings.models import BookingStatus
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from services.permissions import IsLandscaper


# class CompleteLandscaperProfileView(generics.CreateAPIView):
#     serializer_class = LandscaperProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         user = self.request.user

#         # Enforce role
#         if user.role != "landscaper":
#             raise PermissionDenied("Only landscapers can complete this profile.")

#         # Check if profile already exists
#         if hasattr(user, "landscaper_profile"):
#             raise ValidationError("Profile already exists for this user.")

#         # Check subscription
#         subscription = Subscription.objects.filter(user=user, status="active").first()
#         plan_name = subscription.plan.name.lower() if subscription else "basic"

#         # If image is provided but user is not Pro, block it
#         profile_image = serializer.validated_data.get("profile")
#         if profile_image and "pro" not in plan_name:
#             raise PermissionDenied("Only Pro subscription users can upload a profile image.")

#         # Save profile
#         serializer.save()
    
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import LandscaperProfile
from subscriptions.models import Subscription

class CompleteLandscaperProfileView(generics.CreateAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can complete this profile.")

        if hasattr(user, "landscaper_profile"):
            raise ValidationError("Profile already exists.")

        subscription = Subscription.objects.filter(
            user=user,
            status="active"
        ).first()

        plan_name = subscription.plan.name.lower() if subscription else "basic"

        if serializer.validated_data.get("profile") and "pro" not in plan_name:
            raise PermissionDenied(
                "Only Pro subscription users can upload a profile image."
            )

        serializer.save(
            user=user,
            is_profile_completed=True
        )



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



# working houser set

class WorkingHoursListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated, IsLandscaper] 

    def get_queryset(self):
        profile = LandscaperProfile.objects.get(user=self.request.user)
        return WorkingHours.objects.filter(landscaper=profile).order_by("day")

    def create(self, request, *args, **kwargs):
        try:
            profile = LandscaperProfile.objects.get(user=request.user)
        except LandscaperProfile.DoesNotExist:
            return Response(
                {"detail": "Landscaper profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        VALID_DAYS = [choice[0] for choice in DAYS_OF_WEEK]

        data = request.data
        created_hours = []
        errors = []

        # ===============================
        # CASE 1: MULTI-DAY SELECT (DICT)
        # ===============================
        if isinstance(data, dict):
            days = data.get("days")
            start_time = data.get("start_time")
            end_time = data.get("end_time")

            if not isinstance(days, list):
                return Response(
                    {"detail": "`days` must be a list."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not start_time or not end_time:
                return Response(
                    {"detail": "start_time and end_time are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if start_time >= end_time:
                return Response(
                    {"detail": "start_time must be before end_time."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete only selected days
            WorkingHours.objects.filter(
                landscaper=profile,
                day__in=days
            ).delete()

            for day in days:
                if day not in VALID_DAYS:
                    errors.append({"day": day, "detail": "Invalid day"})
                    continue

                created_hours.append(
                    WorkingHours.objects.create(
                        landscaper=profile,
                        day=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                )

        # ===============================
        # CASE 2: LEGACY LIST PAYLOAD
        # ===============================
        elif isinstance(data, list):
            WorkingHours.objects.filter(landscaper=profile).delete()

            for idx, item in enumerate(data):
                day = item.get("day")
                start_time = item.get("start_time")
                end_time = item.get("end_time")

                if day not in VALID_DAYS:
                    errors.append({"index": idx, "detail": "Invalid day"})
                    continue

                if not start_time or not end_time:
                    errors.append({"index": idx, "detail": "Missing time"})
                    continue

                if start_time >= end_time:
                    errors.append({"index": idx, "detail": "start_time must be before end_time"})
                    continue

                created_hours.append(
                    WorkingHours.objects.create(
                        landscaper=profile,
                        day=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                )

        else:
            return Response(
                {"detail": "Invalid payload format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(created_hours, many=True)

        return Response(
            {
                "created_hours": serializer.data,
                "errors": errors
            },
            status=status.HTTP_201_CREATED if created_hours else status.HTTP_400_BAD_REQUEST
        )
