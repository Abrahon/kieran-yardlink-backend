


from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from jobs.serializers import CompletedJobSerializer,ManualOneTimeJobCreateSerializer
from jobs.models import Job, JobItem
from jobs.serializers import (
    JobSerializer,
    JobImageSerializer,
    JobRescheduleSerializer,
    JobItemSerializer,
)

from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.services import send_push_notification
from rest_framework import generics, permissions, status
from rest_framework.response import Response




# @receiver(post_save, sender=Job)
# def job_created(sender, instance, created, **kwargs):
#     if created:
#         send_push_notification(
#             user=instance.assigned_user,
#             title="New Job",
#             message="You got a new job",
#             notification_type="job",
#         )

@receiver(post_save, sender=Job)
def job_created(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.client:
        user = instance.client.user
    elif instance.external_client:
        user = instance.external_client
    else:
        return

    # do your logic here (notification etc.)




class UpcomingJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper_profile = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper_profile:
            return Job.objects.none()

        return Job.objects.filter(
            landscaper=landscaper_profile,
            status=Job.Status.UPCOMING,
            is_active=True
        ).order_by("scheduled_date", "scheduled_time")


# --- Job Detail ---
class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()
        return Job.objects.filter(landscaper=landscaper)



# --- In Progress Job List ---
class InProgressJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()

        return Job.objects.filter(
            landscaper=landscaper,
            status=Job.Status.IN_PROGRESS,
            is_active=True
        ).order_by("scheduled_date", "scheduled_time")




# --- In Progress Job Detail ---
class InProgressJobDetailView(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()

        return Job.objects.filter(
            landscaper=landscaper,
            status=Job.Status.IN_PROGRESS,
            is_active=True
        )



# completd jobs list
class CompletedJobsListView(generics.ListAPIView):
    serializer_class = CompletedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()

        return Job.objects.filter(
            landscaper=landscaper,
            status=Job.Status.COMPLETED,
            is_active=True
        ).order_by("-completed_at", "-updated_at")




# --- Toggle One Job Item Complete / Incomplete ---
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def toggle_job_item_completion(request, item_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

    try:
        item = JobItem.objects.select_related("job").get(
            id=item_id,
            job__landscaper=landscaper
        )
    except JobItem.DoesNotExist:
        return Response({"error": "Job item not found."}, status=status.HTTP_404_NOT_FOUND)

    is_completed = request.data.get("is_completed", None)
    if is_completed is None:
        return Response({"error": "is_completed field is required."}, status=status.HTTP_400_BAD_REQUEST)

    # handle true/false safely from JSON
    if is_completed is True:
        item.mark_complete(user=request.user)
    elif is_completed is False:
        item.mark_incomplete()
    else:
        return Response({"error": "is_completed must be true or false."}, status=status.HTTP_400_BAD_REQUEST)

    item.job.refresh_from_db()

    return Response({
        "message": "Job item updated successfully.",
        "item_id": item.id,
        "item_name": item.name,
        "is_completed": item.is_completed,
        "job_id": item.job.id,
        "job_status": item.job.status,
        "total_price": str(item.job.total_price),
        "completed_items": item.job.completed_items,
        "total_items": item.job.total_items,
    }, status=status.HTTP_200_OK)




# --- Add Job Image ---
class JobImageCreateView(generics.CreateAPIView):
    serializer_class = JobImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        job = serializer.validated_data.get("job")
        landscaper = getattr(self.request.user, "landscaper_profile", None)

        if not landscaper:
            raise serializers.ValidationError({"error": "Landscaper profile not found."})

        if not job:
            raise serializers.ValidationError({"error": "Job is required."})

        if job.landscaper != landscaper:
            raise serializers.ValidationError({"error": "You cannot upload images for this job."})

        if job.status != Job.Status.COMPLETED:
            raise serializers.ValidationError({
                "error": "Images can only be uploaded after all services are completed."
            })

        serializer.save(uploaded_by=self.request.user)




# --- Add Job Reschedule ---
class JobRescheduleCreateView(generics.CreateAPIView):
    serializer_class = JobRescheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            raise serializers.ValidationError({"error": "Landscaper profile not found."})

        job = serializer.validated_data.get("job")
        if not job:
            raise serializers.ValidationError({"error": "Job is required for rescheduling."})

        if job.landscaper != landscaper:
            raise serializers.ValidationError({"error": "You cannot reschedule this job."})

        if job.status == Job.Status.COMPLETED:
            raise serializers.ValidationError({"error": "Cannot reschedule a completed job."})

        serializer.save(
            requested_by=self.request.user,
            old_date=job.scheduled_date,
            old_time=job.scheduled_time
        )




# --- Add or Update Note to Job ---
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def add_job_note(request, job_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

    try:
        job = Job.objects.get(id=job_id, landscaper=landscaper)
    except Job.DoesNotExist:
        return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

    note = request.data.get("note", None)
    if note is None:
        return Response({"error": "Note field is required."}, status=status.HTTP_400_BAD_REQUEST)

    job.note = note
    job.save(update_fields=["note", "updated_at"])

    return Response({
        "message": "Note updated successfully.",
        "note": job.note
    }, status=status.HTTP_200_OK)




# manual job created


class ManualOneTimeJobCreateView(generics.CreateAPIView):
    serializer_class = ManualOneTimeJobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)


