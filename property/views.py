from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .enums import GrassTypeChoices
from rest_framework import status

from .models import Property, PropertyPhoto
from .serializers import PropertyPhotoSerializer

# properties/views.py
from rest_framework import generics, permissions
from .models import Property, PropertyPhoto
from .serializers import PropertySerializer, PropertyPhotoSerializer

# ------------------ Property Views ------------------

class PropertyListCreateView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return properties of the logged-in user
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only access their own properties
        return self.queryset.filter(owner=self.request.user)





from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Property, PropertyPhoto
from .serializers import PropertyPhotoSerializer

class PropertyMultipleImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        property_id = request.data.get("property_id")

        if not property_id:
            return Response(
                {"error": "property_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure property exists
        try:
            property_obj = Property.objects.get(id=int(property_id))
        except Property.DoesNotExist:
            return Response(
                {"error": "Property with this ID does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership
        if property_obj.owner != request.user:
            return Response(
                {"error": "You do not have permission to upload images to this property"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get uploaded images
        images = request.FILES.getlist("images")
        if not images:
            return Response(
                {"error": "images array is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create photos
        photos = []
        for image in images:
            photo = PropertyPhoto.objects.create(property=property_obj, image=image)
            photos.append(photo)

        serializer = PropertyPhotoSerializer(photos, many=True)

        return Response(
            {
                "message": "Images uploaded successfully",
                "images": serializer.data,
            },
            status=status.HTTP_201_CREATED
        )
