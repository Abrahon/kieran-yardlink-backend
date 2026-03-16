# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes
# from django.db import transaction
# from django.utils import timezone

# from jobs.models import Job, JobImage, JobReschedule
# from jobs.serializers import JobSerializer, JobImageSerializer, JobRescheduleSerializer


# # --- Upcoming Jobs for Logged-in Landscaper ---




# from rest_framework import generics, permissions
# from rest_framework.response import Response
# from jobs.models import Job
# from jobs.serializers import JobSerializer

# # class UpcomingJobsListView(generics.ListAPIView):
# #     serializer_class = JobSerializer
# #     permission_classes = [permissions.IsAuthenticated]

# # View for upcoming jobs
# class UpcomingJobsListView(generics.ListAPIView):
#     serializer_class = JobSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         # Get the logged-in landscaper profile
#         landscaper_profile = getattr(self.request.user, "landscaper_profile", None)
#         if not landscaper_profile:
#             return Job.objects.none()

#         # Return upcoming jobs assigned to this landscaper
#         return Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.UPCOMING,
#             is_active=True
#         ).order_by("scheduled_date", "scheduled_time")



# # --- Job Detail ---
# class JobDetailView(generics.RetrieveAPIView):
#     serializer_class = JobSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     lookup_field = "id"
#     lookup_url_kwarg = "id"

#     def get_queryset(self):
#         landscaper = getattr(self.request.user, "landscaper_profile", None)
#         if not landscaper:
#             return Job.objects.none()
#         return Job.objects.filter(landscaper=landscaper)



# class AddJobItemsView(generics.CreateAPIView):
#     serializer_class = AddJobItemsSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data, context={"request": request})
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save()

#         return Response({
#             "message": "Job items added successfully.",
#             "job_id": result["job"].id,
#             "status": result["job"].status,
#             "total_price": str(result["job"].total_price),
#             "items": JobItemSerializer(result["items"], many=True).data
#         })


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework import permissions, status
# from jobs.models import JobItem


# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def toggle_job_item_completion(request, item_id):
#     landscaper = getattr(request.user, "landscaper_profile", None)
#     if not landscaper:
#         return Response({"error": "Landscaper profile not found."}, status=403)

#     try:
#         item = JobItem.objects.select_related("job").get(
#             id=item_id,
#             job__landscaper=landscaper
#         )
#     except JobItem.DoesNotExist:
#         return Response({"error": "Job item not found."}, status=404)

#     is_completed = request.data.get("is_completed", None)
#     if is_completed is None:
#         return Response({"error": "is_completed field is required."}, status=400)

#     if bool(is_completed):
#         item.mark_complete(user=request.user)
#     else:
#         item.mark_incomplete()

#     item.job.refresh_from_db()

#     return Response({
#         "message": "Job item updated successfully.",
#         "item_id": item.id,
#         "item_name": item.name,
#         "is_completed": item.is_completed,
#         "job_id": item.job.id,
#         "job_status": item.job.status,
#         "total_price": str(item.job.total_price),
#         "completed_items": item.job.completed_items,
#         "total_items": item.job.total_items,
#     }, status=status.HTTP_200_OK)

# # --- Add Job Image ---
# from rest_framework.parsers import MultiPartParser, FormParser

# class JobImageCreateView(generics.CreateAPIView):
#     serializer_class = JobImageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def perform_create(self, serializer):
#         job = serializer.validated_data.get("job")
#         landscaper = getattr(self.request.user, "landscaper_profile", None)

#         if not landscaper:
#             raise serializers.ValidationError({"error": "Landscaper profile not found."})

#         if not job:
#             raise serializers.ValidationError({"error": "Job is required."})

#         if job.landscaper != landscaper:
#             raise serializers.ValidationError({"error": "You cannot upload images for this job."})

#         if job.status != Job.Status.COMPLETED:
#             raise serializers.ValidationError(
#                 {"error": "Images can only be uploaded after all services are completed."}
#             )

#         serializer.save(uploaded_by=self.request.user)



# # --- Add Job Reschedule ---
# class JobRescheduleCreateView(generics.CreateAPIView):
#     serializer_class = JobRescheduleSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         job = serializer.validated_data.get("job")
#         if not job:
#             raise serializers.ValidationError({"error": "Job is required for rescheduling."})

#         if job.status == Job.Status.COMPLETED:
#             raise serializers.ValidationError({"error": "Cannot reschedule a completed job."})

#         # Set old_date and old_time automatically
#         serializer.save(
#             requested_by=self.request.user,
#             old_date=job.scheduled_date,
#             old_time=job.scheduled_time
#         )


# # --- Add or Update Note to Job ---
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def add_job_note(request, job_id):
#     try:
#         job = Job.objects.get(id=job_id)
#     except Job.DoesNotExist:
#         return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

#     note = request.data.get("note", None)
#     if note is None:
#         return Response({"error": "Note field is required."}, status=status.HTTP_400_BAD_REQUEST)

#     job.note = note
#     job.save(update_fields=["note", "updated_at"])
#     return Response({"message": "Note updated successfully.", "note": job.note}, status=status.HTTP_200_OK)


from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser

from jobs.models import Job, JobItem
from jobs.serializers import (
    JobSerializer,
    JobImageSerializer,
    JobRescheduleSerializer,
    JobItemSerializer,
)


# --- Upcoming Jobs for Logged-in Landscaper ---
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

# completd jobs list



class CompletedJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
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
