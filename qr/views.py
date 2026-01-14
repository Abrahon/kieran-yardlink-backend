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
    permission_classes = []  # open to authenticated users, check in code

    def get(self, request, qr_id):
        # Get QR instance
        qr = get_object_or_404(LandscaperQRCode, id=qr_id)
        landscaper = qr.landscaper

        # Must be logged in
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Login required to view landscaper profile"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if client has previously worked with landscaper
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

        # Serialize landscaper profile
        serializer = PublicLandscaperSerializer(landscaper, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


        
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

