from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import LandscaperQRCode
from .serializers import PublicLandscaperSerializer

class ScanLandscaperQRCodeView(APIView):
    authentication_classes = []   # NO AUTH
    permission_classes = []       # PUBLIC

    def get(self, request, qr_id):
        qr = get_object_or_404(LandscaperQRCode, id=qr_id)
        serializer = PublicLandscaperSerializer(qr.landscaper)
        return Response(serializer.data)
