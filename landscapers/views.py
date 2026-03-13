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
from django.db import transaction
from bookings.models import BookingRequest
from property.models import Property
from profiles.serializers import ClientProfileSerializer
from rest_framework.decorators import api_view, permission_classes

from django.db import transaction

from profiles.serializers import ClientProfileSerializer




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







class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        business = getattr(self.request.user, "landscaper_profile", None)

        if not business:
            return Service.objects.none()

        return Service.objects.filter(business=business)

    def perform_create(self, serializer):
        business = getattr(self.request.user, "landscaper_profile", None)

        if not business:
            raise PermissionDenied("You must have a business profile to create services.")

        serializer.save(business=business)






class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        try:
            business = self.request.user.landscaper_profile
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "success": True,
                "message": "Service deleted successfully."
            },
            status=status.HTTP_200_OK
        )


       
# # custom service request client
# class ClientCustomServiceListCreateView(generics.ListCreateAPIView):
#     """
#     GET  -> client sees own custom service requests
#     POST -> client creates a new custom service request for a landscaper
#     """
#     serializer_class = ClientCustomServiceSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         client = getattr(self.request.user, "clientprofile", None)
#         if not client:
#             return ClientCustomService.objects.none()

#         return ClientCustomService.objects.filter(
#             client=client,
#             is_active=True
#         ).order_by("-created_at")

#     def perform_create(self, serializer):
#         client = getattr(self.request.user, "clientprofile", None)
#         if not client:
#             raise PermissionDenied("Client profile not found.")

#         serializer.save(
#             client=client,
#             status="pending",
#             price=None
#         )

# class ClientCustomServiceRetrieveDestroyView(generics.RetrieveDestroyAPIView):
#     """
#     GET    -> client retrieves one of their own service requests
#     DELETE -> client deletes only if request is still pending
#     """
#     serializer_class = ClientCustomServiceSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         client = getattr(self.request.user, "clientprofile", None)
#         if not client:
#             return ClientCustomService.objects.none()

#         return ClientCustomService.objects.filter(
#             client=client,
#             is_active=True
#         )

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()

#         if instance.status != "pending":
#             return Response(
#                 {"error": "Only pending requests can be deleted."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         instance.delete()
#         return Response(
#             {"message": "Service request deleted successfully."},
#             status=status.HTTP_200_OK
#         )


# # clinet confirm or decline
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def client_confirm_service(request, pk):
#     action = request.data.get("action")

#     if action not in ["confirm", "decline"]:
#         return Response(
#             {"error": "Invalid action. Must be 'confirm' or 'decline'."},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     client = getattr(request.user, "clientprofile", None)
#     if not client:
#         return Response(
#             {"error": "Client profile not found."},
#             status=status.HTTP_403_FORBIDDEN
#         )

#     try:
#         service = ClientCustomService.objects.get(
#             pk=pk,
#             client=client,
#             is_active=True
#         )
#     except ClientCustomService.DoesNotExist:
#         return Response(
#             {"error": "Service not found."},
#             status=status.HTTP_404_NOT_FOUND
#         )

#     if service.status != "accepted":
#         return Response(
#             {"error": "Service is not ready for confirmation."},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     if action == "decline":
#         service.status = "declined"
#         service.save(update_fields=["status", "updated_at"])
#         return Response(
#             {
#                 "message": "Service declined successfully.",
#                 "status": service.status
#             },
#             status=status.HTTP_200_OK
#         )

#     with transaction.atomic():

#         service = ClientCustomService.objects.select_for_update().get(
#             pk=pk,
#             client=client,
#             is_active=True
#         )

#         if service.status != "accepted":
#             return Response(
#                 {"error": "Service is no longer available for confirmation."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         booking = BookingRequest.objects.create(
#             client=service.client,
#             landscaper=service.landscaper,
#             property=service.property,  # ADD THIS
#             service=None,
#             description=f"{service.name}\n\n{service.description or ''}".strip(),
#             booking_type=BookingRequest.BookingType.CUSTOM,
#             scheduled_date=service.preferred_date,   # ADD THIS
#             scheduled_time=service.preferred_time,   # ADD THIS
#             price=service.price,
#             note=service.note,
#             status=BookingRequest.Status.CONFIRMED
#         )

#         service.status = "confirmed"
#         service.booking = booking   # OPTIONAL (good practice)
#         service.save(update_fields=["status", "booking", "updated_at"])

#     return Response(
#         {
#             "message": "Service confirmed successfully.",
#             "status": service.status,
#             "booking_id": booking.id
#         },
#         status=status.HTTP_200_OK
#     )

# # landscapers see pending  request
# class LandscaperCustomServicePendingListView(generics.ListAPIView):
#     """
#     GET -> landscaper sees only pending requests sent to them
#     """
#     serializer_class = ClientCustomServiceSerializer
#     permission_classes = [IsLandscaper]

#     def get_queryset(self):
#         landscaper = getattr(self.request.user, "landscaper_profile", None)
#         if not landscaper:
#             return ClientCustomService.objects.none()

#         return ClientCustomService.objects.filter(
#             landscaper=landscaper,
#             status="pending",
#             is_active=True
#         ).order_by("-created_at")

# views.py




# ================================
# Client Views
# ================================

class ClientCustomServiceListCreateView(generics.ListCreateAPIView):
    """
    GET  -> client sees own custom service requests
    POST -> client creates a new custom service request
           (one-time by default; recurring optional)
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return ClientCustomService.objects.none()
        return ClientCustomService.objects.filter(
            client=client,
            is_active=True
        ).order_by("-created_at")

    def perform_create(self, serializer):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            raise PermissionDenied("Client profile not found.")

        # One-time: preferred_date/time will be null initially
        serializer.save(
            client=client,
            status="pending",
            price=None,
            preferred_date=None,
            preferred_time=None
        )


class ClientCustomServiceRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    """
    GET    -> client retrieves one of their own service requests
    DELETE -> client deletes only if request is still pending
    """
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return ClientCustomService.objects.none()
        return ClientCustomService.objects.filter(
            client=client,
            is_active=True
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != "pending":
            return Response(
                {"error": "Only pending requests can be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(
            {"message": "Service request deleted successfully."},
            status=status.HTTP_200_OK
        )


# client confirm
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def client_confirm_service(request, pk):

#     action = request.data.get("action")

#     if action not in ["confirm", "decline"]:
#         return Response({"error": "Invalid action."}, status=400)

#     client = getattr(request.user, "clientprofile", None)
#     if not client:
#         return Response({"error": "Client profile not found."}, status=403)

#     try:
#         service = ClientCustomService.objects.get(
#             pk=pk,
#             client=client,
#             is_active=True
#         )
#     except ClientCustomService.DoesNotExist:
#         return Response({"error": "Service not found."}, status=404)

#     if service.status != "accepted":
#         return Response({"error": "Service is not ready for confirmation."}, status=400)

#     if action == "decline":
#         service.status = "declined"
#         service.save(update_fields=["status", "updated_at"])

#         return Response({
#             "message": "Service declined successfully.",
#             "status": service.status
#         })

#     if not service.preferred_date or not service.preferred_time:
#         return Response({"error": "Landscaper has not set schedule yet."}, status=400)
#     with transaction.atomic():

#         service = ClientCustomService.objects.select_for_update().get(
#             pk=pk,
#             client=client,
#             is_active=True
#         )

#         # Determine booking type
#         if service.recurring_type == "weekly":
#             booking_type = BookingRequest.BookingType.WEEKLY
#         elif service.recurring_type == "biweekly":
#             booking_type = BookingRequest.BookingType.BIWEEKLY
#         else:
#             booking_type = BookingRequest.BookingType.CUSTOM

#         booking = BookingRequest.objects.create(
#             client=service.client,
#             landscaper=service.landscaper,
#             property=service.property,
#             service=None,
#             description=f"{service.name}\n\n{service.description or ''}".strip(),
#             booking_type=booking_type,
#             recurring_day_of_week=service.recurring_day_of_week,
#             scheduled_date=service.preferred_date,
#             scheduled_time=service.preferred_time,
#             price=service.price,
#             note=service.note,
#             status=BookingRequest.Status.PENDING,
#             is_active=True
#         )
#     if not service.landscaper:
#         return response(
#             {"error": "No Landscaper assign to service"},
#             status=400
#         )

#         service.status = "confirmed"
#         service.booking = booking
#         service.save(update_fields=["status", "booking", "updated_at"])

#     return Response({
#         "message": "Service confirmed successfully.",
#         "status": service.status,
#         "booking_id": booking.id,
#         "custom_service": ClientCustomServiceSerializer(service).data,
#         "client": ClientProfileSerializer(client).data
#     }, status=status.HTTP_200_OK)



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
        service = ClientCustomService.objects.get(
            pk=pk,
            client=client,
            is_active=True
        )
    except ClientCustomService.DoesNotExist:
        return Response({"error": "Service not found."}, status=404)

    if service.status != "accepted":
        return Response({"error": "Service is not ready for confirmation."}, status=400)

    if action == "decline":
        service.status = "declined"
        service.save(update_fields=["status", "updated_at"])
        return Response({
            "message": "Service declined successfully.",
            "status": service.status
        }, status=200)

    if not service.preferred_date or not service.preferred_time:
        return Response({"error": "Landscaper has not set schedule yet."}, status=400)
    with transaction.atomic():
        service = ClientCustomService.objects.select_for_update().get(
            pk=pk,
            client=client,
            is_active=True
        )

        if not service.landscaper:
            return Response(
                {"error": "No landscaper assigned to this service."},
                status=400
            )

        booking = BookingRequest.objects.create(
            client=service.client,
            landscaper=service.landscaper,
            property=service.property,
            service=None,
            description=f"{service.name}\n\n{service.description or ''}".strip(),
            booking_type=booking_type,
            recurring_day_of_week=service.recurring_day_of_week,
            scheduled_date=service.preferred_date,
            scheduled_time=service.preferred_time,
            price=service.price,
            note=service.note,
            status=BookingRequest.Status.PENDING,
            is_active=True
        )

        service.status = "confirmed"
        service.booking = booking
        service.save(update_fields=["status", "booking", "updated_at"])

    return Response({
        "message": "Service confirmed successfully.",
        "status": service.status,
        "booking_id": booking.id,
        "custom_service": ClientCustomServiceSerializer(service).data,
        "client": ClientProfileSerializer(client).data
    }, status=status.HTTP_200_OK)

# ================================
# Landscaper Views
# ================================

class LandscaperCustomServicePendingListView(generics.ListAPIView):
    serializer_class = ClientCustomServiceSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        # Get the landscaper profile for the logged-in user
        try:
            landscaper_profile = self.request.user.landscaper_profile
        except AttributeError:
            return ClientCustomService.objects.none()

        # Filter requests sent to this landscaper profile
        return ClientCustomService.objects.filter(
            landscaper=landscaper_profile,
            status="pending",
            is_active=True
        ).order_by("-created_at")


from django.utils.dateparse import parse_date, parse_time



@api_view(["PATCH"])
@permission_classes([IsLandscaper])
def landscaper_accept_service(request, pk):
    """
    Landscaper accepts pending service:
    - sets price
    - sets scheduled date & time (for one-time)
    """
    price = request.data.get("price")
    scheduled_date_str = request.data.get("scheduled_date")
    scheduled_time_str = request.data.get("scheduled_time")

    if price is None:
        return Response({"error": "Price is required."}, status=400)

    try:
        price = Decimal(price)
        if price <= 0:
            return Response({"error": "Price must be greater than 0."}, status=400)
    except (InvalidOperation, TypeError, ValueError):
        return Response({"error": "Invalid price format."}, status=400)

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=403)

    try:
        service = ClientCustomService.objects.get(
            pk=pk, landscaper=landscaper, status="pending", is_active=True
        )
    except ClientCustomService.DoesNotExist:
        return Response({"error": "Pending service not found."}, status=404)

    # For one-time, date/time must be provided
    if not service.recurring_type:
        if not scheduled_date_str or not scheduled_time_str:
            return Response(
                {"error": "Scheduled date and time are required for one-time service."}, status=400
            )
        scheduled_date = parse_date(scheduled_date_str)
        scheduled_time = parse_time(scheduled_time_str)
        if not scheduled_date or not scheduled_time:
            return Response({"error": "Invalid date or time format."}, status=400)

        service.preferred_date = scheduled_date
        service.preferred_time = scheduled_time

    service.price = price
    service.status = "accepted"
    service.save(update_fields=["price", "preferred_date", "preferred_time", "status", "updated_at"])

    return Response({
        "message": "Service accepted and schedule set successfully.",
        "service_id": service.id,
        "price": str(service.price),
        "status": service.status,
        "scheduled_date": service.preferred_date,
        "scheduled_time": service.preferred_time,
    }, status=200)

# accepet client custom service landscaper
# @api_view(["PATCH"])
# @permission_classes([IsLandscaper])
# def landscaper_accept_service(request, pk):
#     """
#     Accepts custom service and sets price & scheduled date/time
#     """
#     price = request.data.get("price")
#     scheduled_date = request.data.get("scheduled_date")
#     scheduled_time = request.data.get("scheduled_time")

#     if not price:
#         return Response({"error": "Price is required."}, status=400)

#     try:
#         price = Decimal(price)
#         if price <= 0:
#             raise Response({"error": "Price must be > 0"}, status=400)
#     except:
#         return Response({"error": "Invalid price format"}, status=400)

#     service = ClientCustomService.objects.filter(pk=pk, status="pending").first()
#     if not service:
#         return Response({"error": "Pending service not found"}, status=404)

#     service.price = price
#     service.scheduled_date = scheduled_date
#     service.scheduled_time = scheduled_time
#     service.status = "accepted"
#     service.save()

#     return Response({
#         "message": "Service accepted with price & scheduled time.",
#         "service_id": service.id,
#         "price": str(service.price),
#         "scheduled_date": service.scheduled_date,
#         "scheduled_time": service.scheduled_time,
#         "status": service.status
#     })


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
    permission_classes = [permissions.IsAuthenticated, IsLandscaper]

    def get_queryset(self):
        profile = BusinessProfile.objects.filter(user=self.request.user).first()
        if not profile:
            return WorkingHours.objects.none()

        return WorkingHours.objects.filter(
            landscaper=profile
        ).order_by("day", "start_time")

    def create(self, request, *args, **kwargs):

        try:
            profile = BusinessProfile.objects.get(user=request.user)
        except BusinessProfile.DoesNotExist:
            return Response(
                {"detail": "Business profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data

        days = data.get("days")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if not days:
            return Response(
                {"error": "days field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(days, str):
            days = [days]

        VALID_DAYS = [d[0] for d in DAYS_OF_WEEK]

        created_slots = []
        errors = []

        for day in days:

            if day not in VALID_DAYS:
                errors.append({
                    "day": day,
                    "detail": "Invalid day"
                })
                continue

            # check time overlap
            overlapping = WorkingHours.objects.filter(
                landscaper=profile,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if overlapping.exists():
                errors.append({
                    "day": day,
                    "detail": "Slot overlaps existing slot"
                })
                continue

            slot = WorkingHours.objects.create(
                landscaper=profile,
                day=day,
                start_time=start_time,
                end_time=end_time
            )

            created_slots.append(slot)

        serializer = self.get_serializer(created_slots, many=True)

        return Response(
            {
                "created_slots": serializer.data,
                "errors": errors
            },
            status=status.HTTP_201_CREATED
        )

# update
class WorkingHoursUpdateView(generics.UpdateAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [permissions.IsAuthenticated, IsLandscaper]

    def get_queryset(self):
        profile = BusinessProfile.objects.filter(user=self.request.user).first()
        if not profile:
            return WorkingHours.objects.none()

        return WorkingHours.objects.filter(landscaper=profile)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        day = request.data.get("day", instance.day)
        start_time = request.data.get("start_time", instance.start_time)
        end_time = request.data.get("end_time", instance.end_time)

        # check overlap
        overlap = WorkingHours.objects.filter(
            landscaper=instance.landscaper,
            day=day,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(id=instance.id)

        if overlap.exists():
            return Response(
                {"error": "Slot overlaps with existing slot"},
                status=400
            )

        instance.day = day
        instance.start_time = start_time
        instance.end_time = end_time
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# deleet
class WorkingHoursDeleteView(generics.DestroyAPIView):
    serializer_class = WorkingHoursSerializer
    permission_classes = [permissions.IsAuthenticated, IsLandscaper]

    def get_queryset(self):
        profile = BusinessProfile.objects.filter(user=self.request.user).first()
        if not profile:
            return WorkingHours.objects.none()

        return WorkingHours.objects.filter(landscaper=profile)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return Response(
            {"message": "Working hour slot deleted successfully."},
            status=status.HTTP_200_OK
        )
 
# active dective

@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated, IsLandscaper])
def toggle_working_hour(request, pk):

    try:
        profile = BusinessProfile.objects.get(user=request.user)

        slot = WorkingHours.objects.get(
            id=pk,
            landscaper=profile
        )

    except WorkingHours.DoesNotExist:
        return Response(
            {"error": "Slot not found"},
            status=404
        )

    slot.is_active = not slot.is_active
    slot.save()

    return Response({
        "message": "Slot status updated",
        "is_active": slot.is_active
    })



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