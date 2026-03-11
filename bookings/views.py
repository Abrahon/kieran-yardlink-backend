# # bookings/views.py
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from .models import ServiceBooking
# from .serializers import ServiceBookingRescheduleSerializer


# class ServiceBookingRescheduleAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, booking_id):
#         booking = get_object_or_404(ServiceBooking, id=booking_id, client=request.user)

#         serializer = ServiceBookingRescheduleSerializer(booking, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response({
#             "message": "Booking rescheduled successfully",
#             "booking_id": booking.id,
#             "new_date": serializer.data.get("scheduled_date"),
#             "new_time": serializer.data.get("scheduled_time")
#         }, status=status.HTTP_200_OK)





# updated views 
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
from .models import BookingRequest
from .serializers import BookingRequestSerializer
from landscapers.models import BusinessProfile
from rest_framework.exceptions import PermissionDenied

# Client creates booking (one-time, recurring, custom)
class BookingRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return BookingRequest.objects.none()
        return BookingRequest.objects.filter(client=client).order_by("-created_at")

    def perform_create(self, serializer):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            raise PermissionDenied("Client profile not found.")

        serializer.save(client=client, status="pending", price=None)


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
class LandscaperPendingBookingListView(generics.ListAPIView):
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            business = self.request.user.landscaper_profile
        except BusinessProfile.DoesNotExist:
            return BookingRequest.objects.none()
        return BookingRequest.objects.filter(
            status="pending",
            is_active=True
        ).order_by("-created_at")


# Landscaper accepts booking and sets price
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def landscaper_accept_booking(request, pk):
    price = request.data.get("price")
    new_status = request.data.get("status")

    if price is None:
        return Response({"error": "Price is required."}, status=400)
    if new_status != "accepted":
        return Response({"error": "Status must be 'accepted'."}, status=400)

    try:
        price = Decimal(price)
        if price <= 0:
            raise Response({"error": "Price must be greater than 0."}, status=400)
    except (InvalidOperation, TypeError):
        return Response({"error": "Invalid price format."}, status=400)

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=403)

    try:
        booking = BookingRequest.objects.get(pk=pk, is_active=True)
    except BookingRequest.DoesNotExist:
        return Response({"error": "Booking not found."}, status=404)

    if booking.status != "pending":
        return Response({"error": f"Booking already {booking.status}."}, status=400)

    booking.landscaper = landscaper
    booking.price = price
    booking.status = new_status
    booking.save()

    return Response({
        "message": "Booking accepted and price set successfully.",
        "booking_id": booking.id,
        "price": booking.price,
        "status": booking.status
    })
