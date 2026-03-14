from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.utils import timezone

from jobs.models import Job, JobImage, JobReschedule
from jobs.serializers import JobSerializer, JobImageSerializer, JobRescheduleSerializer


# --- Upcoming Jobs for Logged-in Landscaper ---




from rest_framework import generics, permissions
from rest_framework.response import Response
from jobs.models import Job
from jobs.serializers import JobSerializer

# class UpcomingJobsListView(generics.ListAPIView):
#     serializer_class = JobSerializer
#     permission_classes = [permissions.IsAuthenticated]

# View for upcoming jobs
class UpcomingJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get the logged-in landscaper profile
        landscaper_profile = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper_profile:
            return Job.objects.none()

        # Return upcoming jobs assigned to this landscaper
        return Job.objects.filter(
            landscaper=landscaper_profile,
            status=Job.Status.UPCOMING,
            is_active=True
        ).order_by("scheduled_date", "scheduled_time")

# class UpcomingJobsListView(generics.ListAPIView):
#     serializer_class = JobSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         landscaper_profile = getattr(self.request.user, "landscaper_profile", None)
#         if not landscaper_profile:
#             return Job.objects.none()

#         jobs = Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.UPCOMING,
#             is_active=True
#         ).order_by("scheduled_date", "scheduled_time")

#         for job in jobs:
#             job.recalculate_total_price()

#         return jobs


# --- Job Detail ---
class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()
    lookup_field = "id"


# --- Add Job Image ---
class JobImageCreateView(generics.CreateAPIView):
    serializer_class = JobImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(uploaded_by=self.request.user)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})


# --- Add Job Reschedule ---
class JobRescheduleCreateView(generics.CreateAPIView):
    serializer_class = JobRescheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        job = serializer.validated_data.get("job")
        if not job:
            raise serializers.ValidationError({"error": "Job is required for rescheduling."})

        if job.status == Job.Status.COMPLETED:
            raise serializers.ValidationError({"error": "Cannot reschedule a completed job."})

        # Set old_date and old_time automatically
        serializer.save(
            requested_by=self.request.user,
            old_date=job.scheduled_date,
            old_time=job.scheduled_time
        )


# --- Add or Update Note to Job ---
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def add_job_note(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

    note = request.data.get("note", None)
    if note is None:
        return Response({"error": "Note field is required."}, status=status.HTTP_400_BAD_REQUEST)

    job.note = note
    job.save(update_fields=["note", "updated_at"])
    return Response({"message": "Note updated successfully.", "note": job.note}, status=status.HTTP_200_OK)