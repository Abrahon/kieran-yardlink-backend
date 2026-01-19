# bookings/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ServiceBooking
from .serializers import ServiceBookingRescheduleSerializer


class ServiceBookingRescheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(ServiceBooking, id=booking_id, client=request.user)

        serializer = ServiceBookingRescheduleSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Booking rescheduled successfully",
            "booking_id": booking.id,
            "new_date": serializer.data.get("scheduled_date"),
            "new_time": serializer.data.get("scheduled_time")
        }, status=status.HTTP_200_OK)
