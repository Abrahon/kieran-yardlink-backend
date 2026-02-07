from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import BusinessLandscaperProfileSerializer
from subscriptions.models import Subscription
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
from .serializers import WorkingHoursSerializer,ServiceSerializer
from bookings.models import BookingStatus
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from services.permissions import IsLandscaper
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Service
from django.db.models import F, Avg
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import Q
from rest_framework import generics, status
from .serializers import UpdateServiceSerializer
from accounts.models import User
from accounts.enums import RoleChoices
from profiles.models import LandscaperProfilies
from reviews.models import LandscaperReview
from connections.models import ConnectionRequest
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# views.py
class CompleteLandscaperProfileView(generics.CreateAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can complete this profile.")

        if hasattr(user, "landscaper_profile"):
            raise ValidationError("Profile already exists.")

        # Pass user via serializer context instead of invalid 'profile' kwarg
        serializer.context["user"] = user

        serializer.save()


# update views
class UpdateLandscaperProfileView(generics.UpdateAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user

        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can update profile.")

        return user.landscaper_profile



class GetLandscaperProfileView(generics.RetrieveAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return user.landscaper_profile
        except LandscaperProfile.DoesNotExist:
            raise ValidationError("Landscaper profile not found for this user.")

# service views

class CreateServiceView(generics.CreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser, JSONParser]  # <-- added JSONParser

    def perform_create(self, serializer):
        user = self.request.user

        # Only landscapers can create services
        if user.role != "landscaper":
            raise PermissionDenied("Only landscapers can create services.")

        serializer.save(landscaper=user)



class ListServicesView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Service.objects.all()
        params = self.request.query_params

        # Filter by landscaper
        landscaper_id = params.get("landscaper")
        if landscaper_id:
            queryset = queryset.filter(landscaper_id=landscaper_id)

        # Filter by category
        category = params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Filter by standard service
        standard_service = params.get("standard_service")
        if standard_service:
            queryset = queryset.filter(standard_services__contains=[standard_service])

        return queryset


# update custome service
class UpdateServiceView(generics.UpdateAPIView):
    serializer_class = UpdateServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Service.objects.all()
    lookup_field = "id"   # URL will use service id

    def get_object(self):
        service = super().get_object()

        # Only landscapers can update
        if self.request.user.role != "landscaper":
            raise PermissionDenied("Only landscapers can update services.")

        # Only owner can update
        if service.landscaper != self.request.user:
            raise PermissionDenied("You can only update your own services.")

        return service



class LandscaperFind(generics.ListAPIView):
    """
    Search and filter landscapers (BUSINESS PROFILES)
    Optional query params:
    - name: business name (partial match)
    - city: filter by city
    - service: filter by service ID
    - previous_work: 'true' → landscapers client worked with
    """
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = LandscaperProfile.objects.all()
        user = self.request.user
        params = self.request.query_params

        #  Filter by BUSINESS NAME
        name = params.get("name")
        if name:
            queryset = queryset.filter(
                business_name__icontains=name
            )

        #  Filter by city
        city = params.get("city")
        if city:
            queryset = queryset.filter(
                city__icontains=city
            )

        # 🛠 Filter by service ID
        service_id = params.get("service")
        if service_id:
            queryset = queryset.filter(
                services__id=service_id
            )

        #  Filter by previous work
        prev_work = params.get("previous_work")
        if prev_work and prev_work.lower() == "true":
            worked_landscaper_ids = ServiceBooking.objects.filter(
                client=user,
                status=BookingStatus.COMPLETED
            ).values_list("landscaper_id", flat=True)

            queryset = queryset.filter(
                id__in=worked_landscaper_ids
            )

        return queryset.distinct()


# set working hours for landscapers
class WorkingHoursListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]  

    def get_queryset(self):
        profile = LandscaperProfile.objects.filter(
            user=self.request.user
        ).first()

        if not profile:
            return WorkingHours.objects.none()

        return (
            WorkingHours.objects
            .filter(landscaper=profile)
            .order_by("day")
        )

    def create(self, request, *args, **kwargs):
        """
        ✅ BASIC & PRO BOTH can create working hours
        """
        try:
            profile = LandscaperProfile.objects.get(user=request.user)
        except LandscaperProfile.DoesNotExist:
            return Response(
                {"detail": "Business profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        VALID_DAYS = [choice[0] for choice in DAYS_OF_WEEK]
        data = request.data

        created_hours = []
        errors = []

        if not isinstance(data, dict):
            return Response(
                {"detail": "Payload must be an object."},
                status=status.HTTP_400_BAD_REQUEST
            )

        days = data.get("days")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if not isinstance(days, list) or not days:
            return Response(
                {"detail": "`days` must be a non-empty list."},
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

        for day in days:
            if day not in VALID_DAYS:
                errors.append({"day": day, "detail": "Invalid day"})
                continue

            if WorkingHours.objects.filter(
                landscaper=profile,
                day=day
            ).exists():
                errors.append({
                    "day": day,
                    "detail": "Working hours already exist for this day"
                })
                continue

            created_hours.append(
                WorkingHours.objects.create(
                    landscaper=profile,
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                )
            )

        serializer = self.get_serializer(created_hours, many=True)

        return Response(
            {
                "created_hours": serializer.data,
                "errors": errors
            },
            status=status.HTTP_201_CREATED if created_hours else status.HTTP_400_BAD_REQUEST
        )
# updated views
# from rest_framework import generics, permissions
# from .models import StandardService, ClientServicePreference
# from .serializers import StandardServiceSerializer, StandardServiceUpdateByLandscaperSerializer, ClientServicePreferenceSerializer

# # Admin: create and list all services
# class StandardServiceListCreateView(generics.ListCreateAPIView):
#     queryset = StandardService.objects.all()
#     serializer_class = StandardServiceSerializer
#     permission_classes = [permissions.IsAdminUser]

# # Admin & landscaper: update service
# class StandardServiceUpdateView(generics.RetrieveUpdateAPIView):
#     queryset = StandardService.objects.all()
#     permission_classes = [permissions.IsAuthenticated]

#     def get_serializer_class(self):
#         if self.request.user.is_staff:
#             return StandardServiceSerializer  # Admin can update all fields
#         return StandardServiceUpdateByLandscaperSerializer  # landscaper can update price/type/active

# # Client: list all active services
# class StandardServiceListForClientView(generics.ListAPIView):
#     queryset = StandardService.objects.filter(is_active=True)
#     serializer_class = StandardServiceSerializer
#     permission_classes = [permissions.IsAuthenticated]

# # Client: select services and update preference
# class ClientServicePreferenceView(generics.RetrieveUpdateAPIView):
#     serializer_class = ClientServicePreferenceSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         return ClientServicePreference.objects.get_or_create(client=self.request.user.clientprofile)[0]
