from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Job
from .serializers import JobSerializer
from common.permissions import IsClient, IsLandscaper


# -------------------------
# 1️⃣ Client creates a job
# -------------------------
from rest_framework.parsers import MultiPartParser, FormParser

class JobCreateAPIView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 👈 Add this

    def perform_create(self, serializer):
        serializer.save()




# -------------------------
# 2️⃣ Job detail & update
# -------------------------
# from rest_framework.parsers import MultiPartParser, FormParser

# class JobRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
#     queryset = Job.objects.all()
#     serializer_class = JobSerializer
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]  # needed for file uploads

#     def get_object(self):
#         job = super().get_object()
#         # Only client or assigned landscaper can access
#         if self.request.user not in [job.client, job.landscaper]:
#             from rest_framework.exceptions import PermissionDenied
#             raise PermissionDenied("You do not have permission to access this job.")
#         return job

#     def update(self, request, *args, **kwargs):
#         job = self.get_object()
#         user = request.user
#         data = request.data.copy()

#         # Determine allowed fields based on role
#         if user.role == "client" and job.status == "pending":
#             # Client can update schedule & notes before landscaper accepts
#             allowed_fields = ["date", "start_time", "end_time", "notes"]
#         elif user.role == "landscaper" and user == job.landscaper:
#             # Landscaper can update status, final price, notes, and images
#             allowed_fields = ["status", "final_price", "notes", "images"]
#         else:
#             return Response(
#                 {"detail": "You cannot update this job."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Only keep allowed fields
#         filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

#         serializer = self.get_serializer(job, data=filtered_data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()  # images update handled in serializer
#         return Response(serializer.data)
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer

from common.permissions import IsClient, IsLandscaper
from rest_framework.parsers import MultiPartParser, FormParser

# -------------------------
# Job Update / Retrieve
# -------------------------
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied

from .models import Job
from .serializers import JobSerializer
from common.permissions import IsLandscaper  # <- your custom permission

class JobRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]  # <-- only landscapers
    parser_classes = [MultiPartParser, FormParser]  # <-- for file upload

    def get_object(self):
        job = super().get_object()
        if self.request.user != job.landscaper:
            raise PermissionDenied("You do not have permission to access this job.")
        return job

    def update(self, request, *args, **kwargs):
        job = self.get_object()
        user = request.user
        data = request.data.copy()

        # -------------------------
        # Only landscaper can update status, notes, final_price anytime
        # Images only if task is completed
        # -------------------------
        allowed_fields = ["status", "final_price", "notes"]
        if job.status == "completed":
            allowed_fields.append("images")

        # Keep only allowed fields
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}

        serializer = self.get_serializer(job, data=filtered_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# -------------------------
# 3️⃣ List jobs for client/landscaper
# -------------------------
class JobListAPIView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "client":
            return Job.objects.filter(client=user).order_by("-date", "-start_time")
        elif user.role == "landscaper":
            return Job.objects.filter(landscaper=user).order_by("-date", "-start_time")
        else:
            return Job.objects.none()

