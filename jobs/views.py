


from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from jobs.serializers import CompletedJobSerializer,ManualOneTimeJobCreateSerializer,ClientJobDetailSerializer
from jobs.models import Job, JobItem
from jobs.serializers import (
    JobSerializer,
    JobImageSerializer,
    JobRescheduleSerializer,
    JobItemSerializer,
)
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.services import send_push_notification
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils.timezone import now
from rest_framework import generics, permissions
from jobs.models import Job
from jobs.serializers import JobSerializer
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from django.db.models import Q
from payments.enums import PaymentStatus

from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound



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





# class UpcomingJobsListView(generics.ListAPIView):
#     serializer_class = JobSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         landscaper_profile = getattr(
#             self.request.user,
#             "landscaper_profile",
#             None
#         )

#         if not landscaper_profile:
#             return Job.objects.none()

#         today = now().date()

#         # ✅ AUTO MARK PAST JOBS AS MISSED
#         Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.UPCOMING,
#             scheduled_date__lt=today
#         ).update(status=Job.Status.MISSED)

#         queryset = Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.UPCOMING,
#             is_active=True,
#             scheduled_date__gte=today
#         )

#         # filters
#         selected_date = self.request.query_params.get("date")
#         today_flag = self.request.query_params.get("today")

#         if selected_date:
#             queryset = queryset.filter(
#                 scheduled_date=selected_date
#             )

#         elif today_flag == "true":
#             queryset = queryset.filter(
#                 scheduled_date=today
#             )

#         return queryset.order_by(
#             "scheduled_date",
#             "scheduled_time"
#         )

#     def get_queryset(self):
#         landscaper_profile = getattr(
#             self.request.user,
#             "landscaper_profile",
#             None
#         )

#         if not landscaper_profile:
#             return Job.objects.none()

#         today = now().date()

#         # 1. UPDATE ALL JOB STATUSES FIRST (must run BEFORE filtering)
#         jobs = Job.objects.filter(
#             landscaper=landscaper_profile,
#             is_active=True
#         ).prefetch_related("items", "images")

#         for job in jobs:
#             job.update_status_from_items(save=True)

#         # 2. MARK MISSED JOBS
#         Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.UPCOMING,
#             scheduled_date__lt=today
#         ).update(status=Job.Status.MISSED)

#         # 3. NOW BUILD FINAL QUERYSET
#         queryset = Job.objects.filter(
#             landscaper=landscaper_profile,
#             status=Job.Status.IN_PROGRESS,
#             is_active=True
#         )

#         # filters
#         selected_date = self.request.query_params.get("date")
#         today_flag = self.request.query_params.get("today")

#         if selected_date:
#             queryset = queryset.filter(scheduled_date=selected_date)

#         elif today_flag == "true":
#             queryset = queryset.filter(scheduled_date=today)

#         return queryset.order_by("scheduled_date", "scheduled_time")

class UpcomingJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()

        today = now().date()

        jobs = Job.objects.filter(
            landscaper=landscaper,
            is_active=True
        ).prefetch_related("items", "images")

        for job in jobs:
            job.sync_status(save=True)

        # now filter UPCOMING ONLY
        queryset = Job.objects.filter(
            landscaper=landscaper,
            status=Job.Status.UPCOMING,
            is_active=True
        )

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(scheduled_date=date)

        return queryset.order_by("scheduled_date", "scheduled_time")

class ClientUpcomingJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client_profile = getattr(self.request.user, "clientprofile", None)

        if not client_profile:
            return Job.objects.none()

        queryset = Job.objects.filter(
            client=client_profile,
            status=Job.Status.UPCOMING,
            is_active=True
        )

        # 🔹 query params
        selected_date = self.request.query_params.get("date")
        today_flag = self.request.query_params.get("today")

        # ✅ PRIORITY 1: specific date
        if selected_date:
            queryset = queryset.filter(scheduled_date=selected_date)

        # ✅ PRIORITY 2: today
        elif today_flag == "true":
            queryset = queryset.filter(scheduled_date=now().date())

        return queryset.order_by("scheduled_date", "scheduled_time")







class ClientUpcomingServiceDetailView(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        client_profile = getattr(
            self.request.user,
            "clientprofile",
            None
        )

        if not client_profile:
            return Job.objects.none()

        today = now().date()

        # ✅ AUTO MARK EXPIRED UPCOMING JOBS AS MISSED
        Job.objects.filter(
            client=client_profile,
            status=Job.Status.UPCOMING,
            scheduled_date__lt=today
        ).update(status=Job.Status.MISSED)

        # ✅ ONLY FUTURE/TODAY UPCOMING JOBS
        return Job.objects.filter(
            client=client_profile,
            status=Job.Status.UPCOMING,
            is_active=True,
            scheduled_date__gte=today
        )

    def get_object(self):
        queryset = self.get_queryset()

        job_id = self.kwargs.get("id")

        try:
            return queryset.get(id=job_id)

        except Job.DoesNotExist:
            raise NotFound(
                detail="Upcoming service not found."
            )
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
from django.db.models import Q

class InProgressJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        landscaper = getattr(user, "landscaper_profile", None)
        client = getattr(user, "clientprofile", None)

        qs = Job.objects.filter(
            is_active=True
        ).select_related(
            "client",
            "landscaper",
            "booking"
        ).prefetch_related(
            "items",
            "images",
            "reschedules"
        )

        # filter by role
        if landscaper:
            qs = qs.filter(landscaper=landscaper)
        elif client:
            qs = qs.filter(client=client)
        else:
            return Job.objects.none()

        # ✅ IMPORTANT: ensure status is up to date
        for job in qs:
            job.sync_status(save=True)

        # now return ONLY in_progress
        return qs.filter(status=Job.Status.IN_PROGRESS).order_by(
            "-scheduled_date",
            "-scheduled_time"
        )
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







class CompletedJobsListView(generics.ListAPIView):
    serializer_class = CompletedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        landscaper = getattr(user, "landscaper_profile", None)
        client = getattr(user, "clientprofile", None)

        # -------------------------
        # LANDSCAPER VIEW
        # -------------------------
        if landscaper:
            return Job.objects.filter(
                landscaper=landscaper,
                status=Job.Status.COMPLETED,
                is_active=True
            ).order_by("-completed_at", "-updated_at")

        # -------------------------
        # CLIENT VIEW
        # -------------------------
        if client:
            return Job.objects.filter(
                client=client,
                status=Job.Status.COMPLETED,
                is_active=True
            ).order_by("-completed_at", "-updated_at")

        # -------------------------
        # NO PROFILE
        # -------------------------
        return Job.objects.none()




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
#             raise serializers.ValidationError({
#                 "error": "Images can only be uploaded after all services are completed."
#             })

#         serializer.save(uploaded_by=self.request.user)


# class JobImageCreateView(generics.CreateAPIView):
#     serializer_class = JobImageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def perform_create(self, serializer):

#         landscaper = getattr(self.request.user, "landscaper_profile", None)

#         if not landscaper:
#             raise serializers.ValidationError({
#                 "error": "Landscaper profile not found."
#             })

#         # ✅ FIX: get job from request.data (NOT serializer)
#         job_id = self.request.data.get("job")

#         if not job_id:
#             raise serializers.ValidationError({
#                 "error": "Job is required."
#             })

#         try:
#             job = Job.objects.get(id=job_id)
#         except Job.DoesNotExist:
#             raise serializers.ValidationError({
#                 "error": "Job not found."
#             })

#         if job.landscaper != landscaper:
#             raise serializers.ValidationError({
#                 "error": "You cannot upload images for this job."
#             })

#         if job.status != Job.Status.COMPLETED:
#             raise serializers.ValidationError({
#                 "error": "Images can only be uploaded after job completion."
#             })

#         serializer.save(
#             job=job,
#             uploaded_by=self.request.user
#         )

class JobImageCreateView(generics.CreateAPIView):
    serializer_class = JobImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):

        landscaper = getattr(self.request.user, "landscaper_profile", None)

        if not landscaper:
            raise serializers.ValidationError({
                "error": "Landscaper profile not found."
            })

        job_id = self.request.data.get("job")

        if not job_id:
            raise serializers.ValidationError({
                "error": "Job is required."
            })

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError({
                "error": "Job not found."
            })

        if job.landscaper != landscaper:
            raise serializers.ValidationError({
                "error": "You cannot upload images for this job."
            })

        # ✅ FIXED RULE (IMPORTANT)
        # allow only after work starts
        if job.status == Job.Status.UPCOMING:
            raise serializers.ValidationError({
                "error": "Images cannot be uploaded before job starts."
            })

        serializer.save(
            job=job,
            uploaded_by=self.request.user
        )
        
# --- Add Job Reschedule ---
class JobRescheduleCreateView(generics.CreateAPIView):
    serializer_class = JobRescheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        landscaper = getattr(user, "landscaper_profile", None)
        client = getattr(user, "clientprofile", None)

        job = serializer.validated_data.get("job")

        if not job:
            raise serializers.ValidationError({"error": "Job is required."})

        # ✅ allow BOTH client + landscaper
        if landscaper and job.landscaper != landscaper:
            raise serializers.ValidationError({"error": "Not allowed."})

        if client and job.client != client:
            raise serializers.ValidationError({"error": "Not allowed."})

        if job.status == Job.Status.COMPLETED:
            raise serializers.ValidationError({"error": "Cannot reschedule completed job."})

        # ✅ save reschedule record
        reschedule = serializer.save(
            requested_by=user,
            old_date=job.scheduled_date,
            old_time=job.scheduled_time
        )

        # ✅ UPDATE JOB (THIS WAS MISSING)
        job.scheduled_date = reschedule.new_date
        job.scheduled_time = reschedule.new_time
        job.status = Job.Status.RESCHEDULED
        job.save(update_fields=["scheduled_date", "scheduled_time", "status", "updated_at"])




# --- Add or Update Note to Job ---
# @api_view(["PATCH"])
# @permission_classes([permissions.IsAuthenticated])
# def add_job_note(request, job_id):
#     landscaper = getattr(request.user, "landscaper_profile", None)
#     if not landscaper:
#         return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

#     try:
#         job = Job.objects.get(id=job_id, landscaper=landscaper)
#     except Job.DoesNotExist:
#         return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

#     note = request.data.get("note", None)
#     if note is None:
#         return Response({"error": "Note field is required."}, status=status.HTTP_400_BAD_REQUEST)

#     job.note = note
#     job.save(update_fields=["note", "updated_at"])

#     return Response({
#         "message": "Note updated successfully.",
#         "note": job.note
#     }, status=status.HTTP_200_OK)
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def add_job_note(request, job_id):
    user = request.user

    landscaper = getattr(user, "landscaper_profile", None)
    client = getattr(user, "clientprofile", None)

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    # permission check
    if landscaper and job.landscaper != landscaper:
        return Response({"error": "Not allowed"}, status=403)

    if client and job.client != client:
        return Response({"error": "Not allowed"}, status=403)

    action = request.data.get("action", None)
    note = request.data.get("note", None)

    # =========================
    # STATUS UPDATE (OPTIONAL)
    # =========================
    if action:
        if action == "cancel":
            job.status = Job.Status.CANCELLED

        elif action == "skip":
            job.status = Job.Status.SKIPPED

        elif action == "reschedule":
            job.status = Job.Status.RESCHEDULED

        else:
            return Response({"error": "Invalid action"}, status=400)

    # =========================
    # NOTE (ALWAYS ALLOWED)
    # =========================
    if note is not None:
        job.note = note

    job.save(update_fields=["status", "note", "updated_at"])

    return Response({
        "message": "Job updated successfully",
        "job_id": job.id,
        "status": job.status,
        "note": job.note
    }, status=200)


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_job_status(request, job_id):
    user = request.user

    landscaper = getattr(user, "landscaper_profile", None)
    client = getattr(user, "clientprofile", None)

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    # =========================
    # ✅ BLOCK COMPLETED JOBS
    # =========================
    if job.status == Job.Status.COMPLETED:
        return Response(
            {"error": "Completed jobs cannot be modified"},
            status=400
        )

    # =========================
    # AUTH CHECK
    # =========================
    if landscaper and job.landscaper != landscaper:
        return Response({"error": "Not allowed"}, status=403)

    if client and job.client != client:
        return Response({"error": "Not allowed"}, status=403)

    action = request.data.get("action")
    note = request.data.get("note")

    # =========================
    # STATUS RULES
    # =========================
    if action == "cancel":
        # optional: block cancel if already rescheduled today etc.
        job.status = Job.Status.CANCELLED

    elif action == "skip":
        job.status = Job.Status.SKIPPED

    else:
        return Response({"error": "Invalid action"}, status=400)

    # optional note
    if note:
        job.note = note

    job.save(update_fields=["status", "note", "updated_at"])

    return Response({
        "message": f"Job {action}ed successfully",
        "job_id": job.id
    })


from django.utils import timezone
from django.db.models import Q
from rest_framework import generics, permissions

class ProblemJobsListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        landscaper = getattr(user, "landscaper_profile", None)
        client = getattr(user, "clientprofile", None)

        today = timezone.now().date()

        base_qs = Job.objects.filter(is_active=True)

        qs = base_qs.filter(
            Q(status__in=[
                Job.Status.CANCELLED,
                Job.Status.SKIPPED
            ]) |
            Q(scheduled_date__lt=today)
        ).exclude(status=Job.Status.COMPLETED)

        if landscaper:
            qs = qs.filter(landscaper=landscaper)
        elif client:
            qs = qs.filter(client=client)
        else:
            return Job.objects.none()

        return qs.order_by("-updated_at")

# manual job created
class ManualOneTimeJobCreateView(generics.CreateAPIView):
    serializer_class = ManualOneTimeJobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)


from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Job, JobItem, JobImage


class CompletedJobDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        job_id = kwargs.get("pk")

        job = get_object_or_404(
            Job.objects.select_related(
                "client__user",
                "external_client",
                "landscaper",
                "job_property",
                "booking",
            ),
            id=job_id
        )

        # -------------------------
        # CLIENT INFO (SAFE FOR BOTH TYPES)
        # -------------------------
        client_data = {
            "name": job.client_name,
            "email": job.client_email,
            "phone": job.client_phone,
        }

        # -------------------------
        # LANDSCAPER INFO
        # -------------------------
        landscaper_data = {
            "id": job.landscaper.id,
            "business_name": getattr(job.landscaper, "business_name", None),
        }

        # -------------------------
        # PROPERTY INFO
        # -------------------------
        property_data = None
        if job.job_property:
            property_data = {
                "id": job.job_property.id,
                "name": getattr(job.job_property, "name", None),
                "address": getattr(job.job_property, "address", None),
            }

        # -------------------------
        # JOB ITEMS
        # -------------------------
        items_qs = JobItem.objects.filter(job=job).select_related(
            "service",
            "addon",
            "completed_by"
        )

        items_data = []
        for item in items_qs:
            items_data.append({
                "id": item.id,
                "item_type": item.item_type,
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                "is_completed": item.is_completed,
                "completed_at": item.completed_at,
                "note": item.note,
                "service": item.service.name if item.service else None,
                "addon": item.addon.name if item.addon else None,
                "completed_by": item.completed_by.email if item.completed_by else None,
            })

        # -------------------------
        # JOB IMAGES (BEFORE / AFTER GROUPED)
        # -------------------------
        images_qs = JobImage.objects.filter(job=job)

        before_images = []
        after_images = []

        for img in images_qs:
            img_data = {
                "id": img.id,
                "image_url": img.image.url if img.image else None,
                "caption": img.caption,
                "uploaded_by": img.uploaded_by.email if img.uploaded_by else None,
                "created_at": img.created_at,
            }

            if img.image_type == JobImage.ImageType.BEFORE:
                before_images.append(img_data)
            else:
                after_images.append(img_data)

        # -------------------------
        # PROGRESS CALCULATION
        # -------------------------
        total_items = job.total_items
        completed_items = job.completed_items

        progress_percentage = (
            round((completed_items / total_items) * 100, 2)
            if total_items > 0 else 0
        )

        # -------------------------
        # RESPONSE
        # -------------------------
        return Response({
            "id": job.id,

            "status": job.status,
            "payment_status": job.payment_status,
            "is_active": job.is_active,

            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,

            "total_price": float(job.total_price),

            "progress": {
                "total_items": total_items,
                "completed_items": completed_items,
                "percentage": progress_percentage,
            },

            "completed_at": job.completed_at,

            # CLIENT
            "client": client_data,

            # LANDSCAPER
            "landscaper": landscaper_data,

            # PROPERTY
            "property": property_data,

            # ITEMS
            "items": items_data,

            # IMAGES
            "images": {
                "before": before_images,
                "after": after_images,
            }
        })



class ClientUnpaidCompletedJobView(generics.RetrieveAPIView):
    serializer_class = ClientJobDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        client = getattr(self.request.user, "clientprofile", None)

        if not client:
            raise NotFound("Client profile not found")

        job = Job.objects.filter(
            client=client,
            is_active=True,
            status=Job.Status.COMPLETED
        ).filter(
            # 🔥 FIX: handle both invoice + job payment status
            Q(payment_status=PaymentStatus.PENDING) |
            Q(invoice__status__in=["pending", "sent", "draft"]) |
            Q(invoice__isnull=True)
        ).select_related(
            "client",
            "landscaper",
            "landscaper__user",
            "invoice"
        ).prefetch_related(
            "items",
            "images"
        ).order_by("-completed_at").first()

        if not job:
            raise NotFound("No unpaid completed job found")

        return job