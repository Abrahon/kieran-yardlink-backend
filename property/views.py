from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .enums import GrassTypeChoices
from rest_framework import status

from .models import Property, PropertyPhoto
from .serializers import PropertyPhotoSerializer

class GrassTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": key, "label": label}
            for key, label in GrassTypeChoices.choices
        ])





class PropertyMultipleImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        property_id = request.data.get("property_id")
        images = request.FILES.getlist("images[]")  # ARRAY

        if not images:
            return Response(
                {"error": "images[] array is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        property_obj = Property.objects.filter(
            id=property_id,
            owner=request.user
        ).first()

        if not property_obj:
            return Response(
                {"error": "Property not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        photos = [
            PropertyPhoto.objects.create(
                property=property_obj,
                image=image
            )
            for image in images
        ]

        serializer = PropertyPhotoSerializer(photos, many=True)

        return Response(
            {
                "message": "Images uploaded successfully",
                "images": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )
