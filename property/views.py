

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

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PropertySerializer
        return PropertySerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)




# class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
#     serializer_class = PropertySerializer
#     permission_classes = [IsAuthenticated]
#     lookup_url_kwarg = "property_id"

#     def get_queryset(self):
#         # Only allow user to access their own properties
#         return Property.objects.filter(owner=self.request.user)

#     def get_object(self):
#         return get_object_or_404(
#             Property,
#             id=self.kwargs.get("property_id"),
#             owner=self.request.user
#         )

class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

        
# TODO updated 
# properties/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status, generics
# from rest_framework.parsers import MultiPartParser, FormParser
# from cloudinary.uploader import upload
# from django.shortcuts import get_object_or_404

# from .models import Property
# from jobs.models import Job  # your Job model linking Property and LandscaperProfile
# from .serializers import PropertySerializer


# # =========================
# # PROPERTY LIST & CREATE
# # =========================
# class PropertyListCreateView(generics.ListCreateAPIView):
#     """
#     List all properties visible to the user OR create new property (client only)
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = PropertySerializer

#     def get_queryset(self):
#         user = self.request.user

#         # CLIENT: see only own properties
#         if user.role == "client":
#             return Property.objects.filter(owner=user)

#         # LANDSCAPER: see only properties assigned to jobs they are working on
#         if hasattr(user, "landscaper_profile"):
#             return Property.objects.filter(
#                 jobs__landscaper=user.landscaper_profile
#             ).distinct()

#         # fallback: nothing
#         return Property.objects.none()

#     def perform_create(self, serializer):
#         """
#         Only clients can create properties. Owner is auto-set.
#         """
#         if self.request.user.role != "client":
#             raise PermissionError("Only clients can create properties.")
#         serializer.save(owner=self.request.user)


# # =========================
# # PROPERTY DETAIL, UPDATE, DELETE
# # =========================
# class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
#     """
#     Retrieve, update, or delete a property
#     Access rules:
#     - Client: only own properties
#     - Landscaper: only properties linked to jobs they are assigned to
#     """
#     serializer_class = PropertySerializer
#     permission_classes = [IsAuthenticated]
#     lookup_url_kwarg = "property_id"

#     def get_queryset(self):
#         """
#         For generic filtering if needed
#         """
#         user = self.request.user
#         if user.role == "client":
#             return Property.objects.filter(owner=user)
#         if hasattr(user, "landscaper_profile"):
#             return Property.objects.filter(jobs__landscaper=user.landscaper_profile).distinct()
#         return Property.objects.none()

#     def get_object(self):
#         """
#         Get the property object based on access rules
#         """
#         user = self.request.user
#         property_id = self.kwargs.get("property_id")

#         # CLIENT: own property
#         if user.role == "client":
#             return get_object_or_404(Property, id=property_id, owner=user)

#         # LANDSCAPER: assigned property via job
#         if hasattr(user, "landscaper_profile"):
#             return get_object_or_404(
#                 Property,
#                 id=property_id,
#                 jobs__landscaper=user.landscaper_profile
#             )

#         # fallback: deny access
#         return get_object_or_404(Property, id=0)  # will always 404


# # =========================
# # PROPERTY MULTIPLE IMAGE UPLOAD
# # =========================
# class PropertyMultipleImageUploadView(APIView):
#     """
#     Upload multiple images for a property
#     - Client can upload for own property
#     - Landscaper can optionally upload if assigned via job
#     """
#     permission_classes = [IsAuthenticated]
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, property_id=None):
#         if not property_id:
#             return Response({"error": "property_id is required"}, status=status.HTTP_400_BAD_REQUEST)

#         images = request.FILES.getlist("images")
#         if not images:
#             return Response({"error": "Images are required"}, status=status.HTTP_400_BAD_REQUEST)

#         user = request.user

#         # CLIENT: check ownership
#         if user.role == "client":
#             property_obj = get_object_or_404(Property, id=property_id, owner=user)

#         # LANDSCAPER: check job assignment
#         elif hasattr(user, "landscaper_profile"):
#             property_obj = get_object_or_404(Property, id=property_id, jobs__landscaper=user.landscaper_profile)

#         else:
#             return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

#         uploaded_urls = []
#         for image in images:
#             if not image.content_type.startswith("image/"):
#                 return Response({"error": "Only image files are allowed"}, status=status.HTTP_400_BAD_REQUEST)

#             result = upload(
#                 image,
#                 folder="property_photos",
#                 resource_type="image"
#             )
#             uploaded_urls.append(result["secure_url"])

#         property_obj.images = (property_obj.images or []) + uploaded_urls
#         property_obj.save(update_fields=["images"])

#         return Response(
#             {
#                 "message": "Images uploaded successfully",
#                 "property_id": property_obj.id,
#                 "images_count": len(property_obj.images),
#             },
#             status=status.HTTP_200_OK
#         )