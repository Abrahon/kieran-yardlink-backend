# qrcode/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from bookings.models import ServiceBooking, BookingStatus
from .models import LandscaperQRCode



class ScanLandscaperQRCodeView(APIView):
    permission_classes = []

    def get(self, request, qr_id):
        qr = get_object_or_404(LandscaperQRCode, id=qr_id)
        landscaper = qr.landscaper

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Login required to view landscaper profile"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        has_worked = ServiceBooking.objects.filter(
            client=request.user,
            landscaper=landscaper,
            status=BookingStatus.COMPLETED
        ).exists()

        if not has_worked:
            return Response(
                {
                    "detail": "You have not previously worked with this landscaper",
                    "code": "NO_PREVIOUS_WORK"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PublicLandscaperSerializer(landscaper)
        return Response(serializer.data)
