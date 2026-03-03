from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .serializers import BusinessLandscaperProfileSerializer
from subscriptions.models import Subscription
from rest_framework.exceptions import NotFound
from django.db.models import Q
from bookings.models import ServiceBooking
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Addon
from profiles.models import LandscaperProfilies
from .serializers import AddonSerializer

# landscapers/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WorkingHours, DAYS_OF_WEEK
from .serializers import WorkingHoursSerializer,ServiceSerializer
from bookings.models import BookingStatus
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from services.permissions import IsLandscaper
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Service,BusinessProfile
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
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.exceptions import APIException
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count
from .models import Service
from datetime import datetime, timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.exceptions import ValidationError, PermissionDenied, APIException
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from common.permissions import IsLandscaper
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Service, BusinessProfile
from .serializers import ServiceSerializer
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Service
from .serializers import StandardServiceSerializer
from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import ClientCustomService
from profiles.models import ClientProfile
from .serializers import ClientCustomServiceSerializer





# =========================
# CREATE BUSINESS PROFILE
# =========================
class CompleteLandscaperProfileView(generics.CreateAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [IsLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        user = self.request.user

        if BusinessProfile.objects.filter(user=user).exists():
            raise ValidationError({"detail": "Business profile already exists."})

        try:
            with transaction.atomic():
                serializer.context["user"] = user
                serializer.save()
        except Exception as e:
            raise APIException(f"Business profile creation failed: {str(e)}")



# =========================
# UPDATE BUSINESS PROFILE
# =========================
class UpdateBusinessProfileView(generics.UpdateAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [IsLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        try:
            return self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            raise ValidationError("Business profile not found for this user.")


# =========================
# GET BUSINESS PROFILE
# =========================
class GetBusinessProfileView(generics.RetrieveAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [IsLandscaper]

    def get_object(self):
        try:
            return self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            raise ValidationError("Business profile not found for this user.")




# service views

class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            return Service.objects.none()

        return Service.objects.filter(business=business)

    def perform_create(self, serializer):
        try:
            business = self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            raise PermissionDenied("Create a Business Profile first.")

        serializer.save(business=business)


# update custome service
class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            return Service.objects.none()

        return Service.objects.filter(business=business)



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
        profile = BusinessProfile.objects.filter(
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
            profile = BusinessProfile.objects.get(user=request.user)
        except BusinessProfile.DoesNotExist:
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
        





class ClientCustomServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            client = self.request.user.client_profile
        except ClientProfile.DoesNotExist:
            return ClientCustomService.objects.none()

        return ClientCustomService.objects.filter(client=client)

    def perform_create(self, serializer):
        try:
            client = self.request.user.client_profile
        except ClientProfile.DoesNotExist:
            raise PermissionDenied("You must create a Client Profile first.")

        serializer.save(client=client)


class ClientCustomServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            client = self.request.user.client_profile
        except ClientProfile.DoesNotExist:
            return ClientCustomService.objects.none()

        return ClientCustomService.objects.filter(client=client)

# add ons

class AddonListCreateView(generics.ListCreateAPIView):
    serializer_class = AddonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.landscaperprofilies
        except LandscaperProfilies.DoesNotExist:
            return Addon.objects.none()

        return Addon.objects.filter(business=business)

    def perform_create(self, serializer):
        try:
            business = self.request.user.landscaperprofilies
        except LandscaperProfilies.DoesNotExist:
            raise PermissionDenied("Create a business profile first.")

        serializer.save(business=business)

        

class AddonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.landscaperprofilies
        except LandscaperProfilies.DoesNotExist:
            return Addon.objects.none()

        return Addon.objects.filter(business=business)

# 4️⃣ Toggle active/inactive
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def toggle_service_active(request, pk):
    try:
        service = Service.objects.get(pk=pk, landscaper=request.user)
    except Service.DoesNotExist:
        return Response({"error": "Service not found"}, status=404)

    service.is_active = not service.is_active
    service.save()
    return Response({
        "id": service.id,
        "standard_service": service.standard_service,
        "is_active": service.is_active
    })


# service stats 

# class ServiceStatsAPIView(APIView):
#     """
#     Returns statistics for logged-in landscaper's services.
#     """

#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user

#         queryset = Service.objects.filter(landscaper=user)

#         stats = queryset.aggregate(
#             total_services=Count("id"),
#             active_services=Count("id", filter=Q(is_active=True)),
#             seasonal_services=Count("id", filter=Q(category="seasonal")),
#             average_price=Avg("price")
#         )

#         return Response(
#             {
#                 "total_services": stats["total_services"] or 0,
#                 "active_services": stats["active_services"] or 0,
#                 "seasonal_services": stats["seasonal_services"] or 0,
#                 "average_price": round(float(stats["average_price"] or 0), 2),
#             },
#             status=status.HTTP_200_OK
#         )



# views.py
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def service_performance_monthly(request):
    """
    Return total number of services (Service model) created per month for last 12 months.
    """
    user = request.user
    today = now()

    # Generate last 12 months
    month_labels = []
    month_start_dates = []
    for i in range(12):
        month = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_start_dates.append(month)
        month_labels.append(month.strftime("%b %Y"))

    month_labels = list(reversed(month_labels))
    month_start_dates = list(reversed(month_start_dates))

    # Get services created in the last 12 months
    services_qs = Service.objects.filter(
        landscaper=user,
        created_at__gte=month_start_dates[0]
    ).annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')

    # Map counts to month labels
    counts = {label: 0 for label in month_labels}
    for item in services_qs:
        month_label = item['month'].strftime("%b %Y")
        counts[month_label] = item['count']

    return Response({
        "months": month_labels,
        "service_count": counts
    })

# pinned service /unpinned service

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def toggle_service_pin(request, service_id):
    """
    Toggle pin/unpin for a particular service.
    Only the owner (landscaper) can pin their service.
    """
    try:
        service = Service.objects.get(id=service_id, landscaper=request.user)
    except Service.DoesNotExist:
        return Response({"error": "Service not found"}, status=404)

    service.is_pinned = not service.is_pinned
    service.save(update_fields=["is_pinned"])

    return Response({
        "id": service.id,
        "standard_service": service.standard_service,
        "is_pinned": service.is_pinned
    })