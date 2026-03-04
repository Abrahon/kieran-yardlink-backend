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
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist
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
# from .serializers import UpdateServiceSerializer
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
from common .permissions import IsLandscaper





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
            business = self.request.user.landscaper_profile
        except BusinessProfile.DoesNotExist:
            return Service.objects.none()
        return Service.objects.filter(business=business)

    def perform_create(self, serializer):
        try:
            business = self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            raise PermissionDenied("You must create a Business Profile first.")

        try:
            with transaction.atomic():
                serializer.save(business=business)
        except IntegrityError as e:
            # Check if it's a duplicate service name
            if 'unique_service_per_business' in str(e):
                raise ValidationError({
                    "name": "A service with this name already exists for your business."
                })
            else:
                # Other integrity errors
                raise ValidationError({"detail": str(e)})


# update custome service

from django.db import transaction

class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.business_profile
        except BusinessProfile.DoesNotExist:
            return Service.objects.none()
        return Service.objects.filter(business=business)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)  # supports PATCH
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
        except ValidationError as ve:
            return Response(
                {"success": False, "message": "Update failed.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Update failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"success": True, "message": "Service updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )



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
    """
    GET: List all custom services for the logged-in client
    POST: Create a new custom service for the logged-in client
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            client = self.request.user.clientprofile
        except ClientProfile.DoesNotExist:
            return ClientCustomService.objects.none()

        return ClientCustomService.objects.filter(client=client)

    def perform_create(self, serializer):
        try:
            client = self.request.user.clientprofile
        except ClientProfile.DoesNotExist:
            raise PermissionDenied("You must create a Client Profile first.")

        serializer.save(client=client)

    def create(self, request, *args, **kwargs):
        """
        Override to return a friendly success message
        """
        response = super().create(request, *args, **kwargs)
        response.data = {
            "message": "Custom service created successfully.",
            "service": response.data
        }
        return response





class ClientCustomServiceRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve a custom service by ID
    PUT/PATCH: Update the custom service (only owner client can update)
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        try:
            client = self.request.user.clientprofile  # ✅ use clientprofile, not client_profile
        except ClientProfile.DoesNotExist:
            return ClientCustomService.objects.none()

        return ClientCustomService.objects.filter(client=client)

    def perform_update(self, serializer):
        # Ensure only the owner client can update
        try:
            client = self.request.user.client_profile
        except ClientProfile.DoesNotExist:
            raise PermissionDenied("You must have a Client Profile to update services.")

        serializer.save(client=client)

    def update(self, request, *args, **kwargs):
        """
        Override to add a success message
        """
        response = super().update(request, *args, **kwargs)
        response.data = {
            "message": "Custom service updated successfully.",
            "service": response.data
        }
        return response





class ClientCustomServiceDeleteView(generics.DestroyAPIView):
    """
    DELETE: Remove a custom service (only the owner client)
    """
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # ✅ Use clientprofile, not client_profile
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            # Return empty queryset if the user has no client profile
            return ClientCustomService.objects.none()
        return ClientCustomService.objects.filter(client=client)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Custom service deleted successfully."},
            status=status.HTTP_200_OK
        )


# client see the custom service
class LandscaperCustomServiceListView(generics.ListAPIView):
    """
    GET: List all active client custom service requests
    for the authenticated landscaper to view.
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        # Only active requests
        return ClientCustomService.objects.filter(is_active=True).order_by('-created_at')


# accepet client custom service landscaper
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def accept_client_custom_service(request, pk):
    """
    POST: Landscaper accepts a client custom service request
    """
    try:
        service = ClientCustomService.objects.get(pk=pk, is_active=True)
    except ClientCustomService.DoesNotExist:
        return Response({"error": "Service request not found"}, status=404)

    if service.status != "pending":
        return Response({"message": f"Service already {service.status}"}, status=400)

    # Accept the service
    service.status = "accepted"
    service.save()

    return Response({
        "message": "Service request accepted.",
        "id": service.id,
        "name": service.name,
        "status": service.status
    }, status=status.HTTP_200_OK)



# active inactive

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def toggle_client_custom_service_active(request, pk):
    try:
        # ✅ Correct attribute: clientprofile
        service = ClientCustomService.objects.get(pk=pk, client=request.user.clientprofile)
    except ClientCustomService.DoesNotExist:
        return Response({"error": "Service not found"}, status=404)

    service.is_active = not service.is_active
    service.save()

    return Response({
        "message": "Custom service status updated.",
        "id": service.id,
        "name": service.name,
        "is_active": service.is_active
    })



# add ons

# class AddonListCreateView(generics.ListCreateAPIView):
#     serializer_class = AddonSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         try:
#             business = self.request.user.landscaper_profile  # ✅ matches related_name
#             return Addon.objects.filter(business=business)
#         except ObjectDoesNotExist:
#             return Addon.objects.none()

#     def perform_create(self, serializer):
#         try:
#             business = self.request.user.landscaper_profile
#         except ObjectDoesNotExist:
#             raise serializers.ValidationError(
#                 {"error": "Landscaper profile not found."}
#             )

#         serializer.save(business=business)

#     def create(self, request, *args, **kwargs):
#         response = super().create(request, *args, **kwargs)
#         return Response(
#             {
#                 "message": "Addon created successfully.",
#                 "data": response.data
#             },
#             status=status.HTTP_201_CREATED
#         )

class AddonListCreateView(generics.ListCreateAPIView):
    serializer_class = AddonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.landscaper_profile
        except BusinessProfile.DoesNotExist:
            return Addon.objects.none()
        return Addon.objects.filter(business=business)

    def perform_create(self, serializer):
        try:
            business = self.request.user.landscaper_profile
        except BusinessProfile.DoesNotExist:
            raise serializers.ValidationError({"error": "Landscaper profile not found."})

        serializer.save(business=business)

class AddonDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddonSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        try:
            business = self.request.user.landscaper_profile
            return Addon.objects.filter(business=business)
        except ObjectDoesNotExist:
            return Addon.objects.none()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {
                "message": "Addon updated successfully.",
                "data": response.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Soft delete instead of hard delete
        instance.is_active = False
        instance.save()

        return Response(
            {"message": "Addon deactivated successfully."},
            status=status.HTTP_200_OK
        )



# 4️⃣ Toggle active/inactive
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def toggle_service_active(request, pk):
    try:
        service = Service.objects.get(pk=pk, business__user=request.user)
    except Service.DoesNotExist:
        return Response({"error": "Service not found"}, status=404)

    service.is_active = not service.is_active
    service.save()
    return Response({
        "id": service.id,
        "name": service.name,          # updated from standard_service
        "is_active": service.is_active
    })

# service stats 

class ServiceStatsAPIView(APIView):
    """
    Returns statistics for logged-in landscaper's services.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        queryset = Service.objects.filter(landscaper=user)

        stats = queryset.aggregate(
            total_services=Count("id"),
            active_services=Count("id", filter=Q(is_active=True)),
            seasonal_services=Count("id", filter=Q(category="seasonal")),
            average_price=Avg("price")
        )

        return Response(
            {
                "total_services": stats["total_services"] or 0,
                "active_services": stats["active_services"] or 0,
                "seasonal_services": stats["seasonal_services"] or 0,
                "average_price": round(float(stats["average_price"] or 0), 2),
            },
            status=status.HTTP_200_OK
        )



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