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
from decimal import Decimal, InvalidOperation




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
    permission_classes = [IsAuthenticated, IsLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile = getattr(self.request.user, "landscaper_profile", None)

        if not profile:
            raise ValidationError("Business profile not found for this user.")

        return profile


# =========================
# GET BUSINESS PROFILE
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated


class GetBusinessProfileView(generics.RetrieveAPIView):
    serializer_class = BusinessLandscaperProfileSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get_object(self):
        profile = getattr(self.request.user, "landscaper_profile", None)

        if not profile:
            raise ValidationError("Business profile not found for this user.")

        return profile




from django.db import transaction, IntegrityError
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import generics, permissions


class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = getattr(self.request.user, "landscaper_profile", None)

        if not business:
            return Service.objects.none()

        return Service.objects.filter(business=business)

    def perform_create(self, serializer):
        business, _ = BusinessProfile.objects.get_or_create(user=self.request.user)
        try:
            with transaction.atomic():
                serializer.save(business=business)
        except IntegrityError as e:
            if "unique_service_per_business" in str(e):
                raise ValidationError({
                    "name": "A service with this name already exists for your business."
                })
            raise ValidationError({"detail": "Service creation failed."})


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
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return ClientCustomService.objects.none()
        return ClientCustomService.objects.filter(client=client).order_by("-created_at")

    def perform_create(self, serializer):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            raise PermissionDenied("Client profile not found.")

        serializer.save(
            client=client,
            status="pending",
            price=None
        )



class ClientCustomServiceRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return ClientCustomService.objects.none()
        return ClientCustomService.objects.filter(client=client)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != "pending":
            return Response(
                {"error": "Only pending requests can be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.delete()
        return Response({"message": "Service request deleted successfully."})


# clinet confirm or decline
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def client_confirm_service(request, pk):
    action = request.data.get("action")

    if action not in ["confirm", "decline"]:
        return Response({"error": "Invalid action."}, status=400)

    client = getattr(request.user, "clientprofile", None)
    if not client:
        return Response({"error": "Client profile not found."}, status=403)

    try:
        service = ClientCustomService.objects.get(pk=pk, client=client)
    except ClientCustomService.DoesNotExist:
        return Response({"error": "Service not found."}, status=404)

    if service.status != "accepted":
        return Response(
            {"error": "Service is not ready for confirmation."},
            status=400
        )

    if action == "confirm":
        service.status = "confirmed"
    else:
        service.status = "declined"

    service.save()

    return Response({
        "message": f"Service {service.status} successfully.",
        "status": service.status
    })


# landscapers
# client see the custom service
class LandscaperCustomServiceListView(generics.ListAPIView):
    """
    GET: List all active client custom service requests
    for the authenticated landscaper to view.
    Shows pending requests.
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        # Optional: check if user has a profile
        try:
            self.request.user.landscaper_profile
        except BusinessProfile.DoesNotExist:
            return ClientCustomService.objects.none()

        return ClientCustomService.objects.filter(
            is_active=True,
            status="pending"  # only pending requests
        ).order_by("-created_at")



# accepet client custom service landscaper



@api_view(["PATCH"])
@permission_classes([IsLandscaper])
def landscaper_accept_service(request, pk):
    """
    PATCH: Landscaper sets price and updates status (must be 'accepted')
    """

    price = request.data.get("price")
    new_status = request.data.get("status")

    # ✅ Validate required fields
    if price is None:
        return Response(
            {"error": "Price is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if new_status != "accepted":
        return Response(
            {"error": "Status must be 'accepted'."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Validate price format
    try:
        price = Decimal(price)
        if price <= 0:
            return Response(
                {"error": "Price must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST
            )
    except (InvalidOperation, TypeError):
        return Response(
            {"error": "Invalid price format."},
            status=status.HTTP_400_BAD_REQUEST
        )
    landscaper = getattr(request.user, "landscaper_profile", None)

    try:
        service = ClientCustomService.objects.get(
            pk=pk,
            is_active=True
        )
    except ClientCustomService.DoesNotExist:
        return Response(
            {"error": "Service not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # ✅ Only allow from pending → accepted
    if service.status != "pending":
        return Response(
            {"error": f"Service already {service.status}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Update service
    service.landscaper = landscaper
    service.price = price
    service.status = new_status
    service.save()

    return Response(
        {
            "message": "Service accepted and price set successfully.",
            "service_id": service.id,
            "price": service.price,
            "status": service.status
        },
        status=status.HTTP_200_OK
    )


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