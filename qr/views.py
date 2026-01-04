from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import LandscaperQRCode
from .serializers import PublicLandscaperSerializer
from bookings.models import ServiceBooking   # example app

class ScanLandscaperQRCodeView(APIView):
    permission_classes = []  # client may or may not be logged in

    def get(self, request, qr_id):
        qr = get_object_or_404(LandscaperQRCode, id=qr_id)
        landscaper = qr.landscaper

        client = request.user if request.user.is_authenticated else None

        # Client must be logged in to verify history
        if not client:
            return Response(
                {"detail": "Login required to view landscaper profile"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check previous completed work
        has_worked = Job.objects.filter(
            client=client,
            landscaper=landscaper,
            status="completed"
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
