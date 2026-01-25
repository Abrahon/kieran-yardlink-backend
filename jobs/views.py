from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Job
from .serializers import JobSerializer
from cloudinary.uploader import upload  # Cloudinary uploader

class JobCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new job with multiple images.
        """
        data = request.data.copy()  # make mutable copy
        images_files = request.FILES.getlist("images")

        uploaded_urls = []
        for image in images_files:
            result = upload(image, folder="job_images")
            uploaded_urls.append(result["secure_url"])

        # Store URLs in the same 'images' field
        data["images"] = uploaded_urls

        serializer = JobSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class JobUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        """
        Update an existing job and append/replace images.
        """
        job = get_object_or_404(Job, id=pk)

        if request.user != job.landscaper and request.user != job.client:
            return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        new_images = request.FILES.getlist("images")

        uploaded_urls = job.images or []  # existing images

        for image in new_images:
            result = upload(image, folder="job_images")
            uploaded_urls.append(result["secure_url"])

        data["images"] = uploaded_urls  # store all URLs in same field

        serializer = JobSerializer(job, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
