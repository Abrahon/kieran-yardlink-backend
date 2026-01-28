from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from bookings.models import ServiceBooking, BookingStatus
from .models import LandscaperQRCode
from .serializers import PublicLandscaperSerializer  # make sure this exists
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import LandscaperQRCode
from .utils import generate_landscaper_qr  # the function we wrote earlier



class ScanLandscaperQRCodeView(APIView):
    """
    Client scans QR → sees landscaper public profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, qr_id):
        # Only clients can scan
        if request.user.role != "client":
            return Response(
                {"detail": "Only clients can scan landscaper QR codes"},
                status=status.HTTP_403_FORBIDDEN
            )

        qr = get_object_or_404(LandscaperQRCode, id=qr_id)
        landscaper = qr.landscaper

        serializer = PublicLandscaperSerializer(
            landscaper,
            context={"request": request}
        )

        return Response({
            "scanned": True,
            "landscaper": serializer.data
        }, status=status.HTTP_200_OK)

        
# generate qr code
# qrcode/views.py
class GenerateQRCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Ensure user is a landscaper
        if user.role != "landscaper":
            return Response({"detail": "Only landscapers can generate QR codes"}, status=403)

        # Create or get existing QR
        qr_instance, created = LandscaperQRCode.objects.get_or_create(landscaper=user.landscaper_profile)

        qr_image_path = generate_landscaper_qr(qr_instance)

        return Response({
            "qr_id": str(qr_instance.id),
            "qr_url": f"http://localhost:3000/scan/{qr_instance.id}",  # frontend URL
            "qr_image_path": qr_image_path
        })

