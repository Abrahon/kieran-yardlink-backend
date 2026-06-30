

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from cloudinary.uploader import upload
from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework import generics
from .serializers import PropertySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Property
from .serializers import PropertySerializer




from .models import Property
class PropertyMultipleImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, property_id=None):  # accept property_id from URL
        images = request.FILES.getlist("images")

        if not property_id:
            return Response(
                {"error": "property_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not images:
            return Response(
                {"error": "Images are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            property_obj = Property.objects.get(
                id=property_id,
                owner=request.user
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found or access denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        uploaded_urls = []
        for image in images:
            if not image.content_type.startswith("image/"):
                return Response(
                    {"error": "Only image files are allowed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = upload(
                image,
                folder="property_photos",
                resource_type="image"
            )
            uploaded_urls.append(result["secure_url"])

        property_obj.images = (property_obj.images or []) + uploaded_urls
        property_obj.save(update_fields=["images"])

        return Response(
            {
                "message": "Images uploaded successfully",
                "property_id": property_obj.id,
                "images_count": len(property_obj.images),
            },
            status=200
        )



class PropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropertySerializer

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        images = self.request.data.get("images", [])

        # ensure list safety
        if images is None:
            images = []

        serializer.save(
            owner=self.request.user,
            is_active=True,
            images=images  # ✅ IMPORTANT FIX
        )




class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return Property.objects.filter(
            owner=self.request.user
        )

    # UPDATE / ACTIVATE / DEACTIVATE
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Property updated successfully",
            "data": serializer.data
        })

    # PERMANENT DELETE
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        instance.delete()

        return Response({
            "message": "Property deleted successfully"
        }, status=status.HTTP_200_OK)