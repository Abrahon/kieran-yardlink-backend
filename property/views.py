from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from cloudinary.uploader import upload
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Property
from .serializers import PropertySerializer

from .models import Property


class PropertyMultipleImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        property_id = request.data.get("property_id")
        images = request.FILES.getlist("images")
        replace_images = request.data.get("replace_images", False)

        if not property_id or not images:
            return Response(
                {"error": "property_id and images are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            property_obj = Property.objects.get(
                id=int(property_id),
                owner=request.user
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        uploaded_urls = []
        for image in images:
            result = upload(image, folder="property_photos")
            uploaded_urls.append(result["secure_url"])

        if replace_images:
            property_obj.images = uploaded_urls
        else:
            property_obj.images = (property_obj.images or []) + uploaded_urls

        property_obj.save(update_fields=["images"])

        return Response(
            {
                "message": "Images uploaded successfully",
                "property_id": property_obj.id,
                "images": property_obj.images,
            },
            status=status.HTTP_200_OK
        )
class PropertyImagesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, property_id):
        try:
            property_obj = Property.objects.get(
                id=int(property_id),
                owner=request.user
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "property_id": property_obj.id,
                "images": property_obj.images
            },
            status=status.HTTP_200_OK
        )

class PropertyListCreateView(generics.ListCreateAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)
