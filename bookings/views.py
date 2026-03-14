





# updated views 
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
from .models import BookingRequest
from .serializers import BookingRequestSerializer
from landscapers.models import BusinessProfile
from rest_framework.exceptions import PermissionDenied



# Landscaper sees pending bookings
# Landscaper sees pending bookings
class LandscaperPendingBookingListView(generics.ListAPIView):
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)

        if not landscaper:
            return BookingRequest.objects.none()

        qs = BookingRequest.objects.filter(landscaper=landscaper)
        print("all for landscaper:", qs.count())

        qs2 = qs.filter(status=BookingRequest.Status.PENDING)
        print("pending only:", qs2.count())

        qs3 = qs2.filter(is_active=True)
        print("pending + active:", qs3.count())

        return qs3.order_by("-created_at")


# accept booking
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def landscaper_accept_booking(request, pk):

#     price = request.data.get("price")

#     if price is None:
#         return Response({"error": "Price is required."}, status=400)

#     try:
#         price = Decimal(price)
#     except:
#         return Response({"error": "Invalid price."}, status=400)

#     landscaper = getattr(request.user, "landscaper_profile", None)

#     if not landscaper:
#         return Response({"error": "Landscaper profile not found."}, status=403)

#     try:
#         booking = BookingRequest.objects.get(
#             pk=pk,
#             status=BookingRequest.Status.PENDING,
#             is_active=True
#         )
#     except BookingRequest.DoesNotExist:
#         return Response({"error": "Booking not found."}, status=404)

#     booking.landscaper = landscaper
#     booking.price = price
#     booking.status = BookingRequest.Status.ACCEPTED
#     booking.job_created = True

#     booking.save(update_fields=[
#         "landscaper",
#         "price",
#         "status",
#         "job_created",
#         "updated_at"
#     ])

#     return Response({
#         "message": "Booking accepted and job created.",
#         "booking_id": booking.id,
#         "job_id": booking.id,
#         "status": booking.status
#     })

# from decimal import Decimal, InvalidOperation
# from django.db import transaction
# from rest_framework import permissions, status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response


# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def landscaper_accept_booking(request, pk):
#     landscaper = getattr(request.user, "landscaper_profile", None)

#     if not landscaper:
#         return Response({"error": "Landscaper profile not found."}, status=403)

#     with transaction.atomic():
#         try:
#             booking = BookingRequest.objects.select_for_update().get(
#                 pk=pk,
#                 landscaper=landscaper,
#                 status=BookingRequest.Status.PENDING,
#                 is_active=True
#             )
#         except BookingRequest.DoesNotExist:
#             return Response({"error": "Pending booking not found."}, status=404)

#         if booking.job_created:
#             return Response(
#                 {"error": "Job already created for this booking."},
#                 status=400
#             )

#         # Create job from booking
#         job = Job.objects.create(
#             booking=booking,
#             client=booking.client,
#             landscaper=booking.landscaper,
#             property=booking.property,
#             scheduled_date=booking.scheduled_date,
#             scheduled_time=booking.scheduled_time,
#             price=booking.price,
#             description=booking.description,
#             status=Job.Status.UPCOMING,
#             is_active=True
#         )

#         booking.status = BookingRequest.Status.ACCEPTED
#         booking.job_created = True
#         booking.save(update_fields=["status", "job_created", "updated_at"])

#     return Response({
#         "message": "Booking accepted and job created successfully.",
#         "booking_id": booking.id,
#         "job_id": job.id,
#         "booking_status": booking.status
#     }, status=status.HTTP_200_OK)

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from bookings.models import BookingRequest
from jobs.models import Job


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def landscaper_accept_booking(request, pk):
    landscaper = getattr(request.user, "landscaper_profile", None)

    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=403)

    with transaction.atomic():
        try:
            booking = BookingRequest.objects.select_for_update().get(
                pk=pk,
                landscaper=landscaper,
                status=BookingRequest.Status.PENDING,
                is_active=True
            )
        except BookingRequest.DoesNotExist:
            return Response({"error": "Pending booking not found."}, status=404)

        if booking.job_created:
            return Response(
                {"error": "Job already created for this booking."},
                status=400
            )

        job = Job.objects.create(
            booking=booking,
            client=booking.client,
            landscaper=booking.landscaper,
            scheduled_date=booking.scheduled_date,
            scheduled_time=booking.scheduled_time,
            total_price=booking.price or 0,
            status=Job.Status.UPCOMING,
            is_active=True
        )


        booking.status = BookingRequest.Status.ACCEPTED
        booking.job_created = True
        booking.save(update_fields=["status", "job_created", "updated_at"])

    return Response({
        "message": "Booking accepted and job created successfully.",
        "booking_id": booking.id,
        "job_id": job.id,
        "booking_status": booking.status,
        "booking_price": float(booking.price) if booking.price is not None else 0,
        "job_total_price": float(job.total_price) if job.total_price is not None else 0,
    }, status=status.HTTP_200_OK)


class ClientBookingListView(generics.ListAPIView):

    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        client = getattr(self.request.user, "clientprofile", None)

        if not client:
            return BookingRequest.objects.none()

        return BookingRequest.objects.filter(
            client=client,
            is_active=True
        ).order_by("-created_at")


# Client creates booking (one-time, recurring, custom)
# class BookingRequestListCreateView(generics.ListCreateAPIView):
#     serializer_class = BookingRequestSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         client = getattr(self.request.user, "clientprofile", None)
#         if not client:
#             return BookingRequest.objects.none()
#         return BookingRequest.objects.filter(client=client).order_by("-created_at")

#     def perform_create(self, serializer):
#         client = getattr(self.request.user, "clientprofile", None)
#         if not client:
#             raise PermissionDenied("Client profile not found.")

#         serializer.save(client=client, status="pending", price=None)


# Client can view / delete only pending requests
class BookingRequestRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return BookingRequest.objects.none()
        return BookingRequest.objects.filter(client=client)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != "pending":
            return Response(
                {"error": "Only pending bookings can be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response({"message": "Booking deleted successfully."})


# Client confirm/decline price set by landscaper
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def client_confirm_booking(request, pk):
    action = request.data.get("action")
    if action not in ["confirm", "decline"]:
        return Response({"error": "Invalid action."}, status=400)

    client = getattr(request.user, "clientprofile", None)
    if not client:
        return Response({"error": "Client profile not found."}, status=403)

    try:
        booking = BookingRequest.objects.get(pk=pk, client=client)
    except BookingRequest.DoesNotExist:
        return Response({"error": "Booking not found."}, status=404)

    if booking.status != "accepted":
        return Response({"error": "Booking is not ready for confirmation."}, status=400)

    booking.status = "confirmed" if action == "confirm" else "declined"
    booking.save()

    return Response({"message": f"Booking {booking.status} successfully.", "status": booking.status})


# Landscaper views pending bookings
# class LandscaperPendingBookingListView(generics.ListAPIView):
#     serializer_class = BookingRequestSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         try:
#             business = self.request.user.landscaper_profile
#         except BusinessProfile.DoesNotExist:
#             return BookingRequest.objects.none()
#         return BookingRequest.objects.filter(
#             status="pending",
#             is_active=True
#         ).order_by("-created_at")


# Landscaper accepts booking and sets price
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def landscaper_accept_booking(request, pk):
#     price = request.data.get("price")
#     new_status = request.data.get("status")

#     if price is None:
#         return Response({"error": "Price is required."}, status=400)
#     if new_status != "accepted":
#         return Response({"error": "Status must be 'accepted'."}, status=400)

#     try:
#         price = Decimal(price)
#         if price <= 0:
#             raise Response({"error": "Price must be greater than 0."}, status=400)
#     except (InvalidOperation, TypeError):
#         return Response({"error": "Invalid price format."}, status=400)

#     landscaper = getattr(request.user, "landscaper_profile", None)
#     if not landscaper:
#         return Response({"error": "Landscaper profile not found."}, status=403)

#     try:
#         booking = BookingRequest.objects.get(pk=pk, is_active=True)
#     except BookingRequest.DoesNotExist:
#         return Response({"error": "Booking not found."}, status=404)

#     if booking.status != "pending":
#         return Response({"error": f"Booking already {booking.status}."}, status=400)

#     booking.landscaper = landscaper
#     booking.price = price
#     booking.status = new_status
#     booking.save()

#     return Response({
#         "message": "Booking accepted and price set successfully.",
#         "booking_id": booking.id,
#         "price": booking.price,
#         "status": booking.status
#     })
