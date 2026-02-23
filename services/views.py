
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from common.permissions import IsClient, IsAdmin, IsLandscaper
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import NotFound
from landscapers.models import WorkingHours, LandscaperProfile, Service
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import F
from services.models import ServiceSchedule, PaymentStatus
from django.utils import timezone
from accounts.models import User
from payments.serializers import PaymentHistorySerializer
from rest_framework import generics, status
from .models import ClientService, ClientServicePreference, ServiceSchedule, ScheduleCompletionImage
from .serializers import (
    ServiceSerializer,
    ClientServicePreferenceWriteSerializer,
    ClientServicePreferenceReadSerializer,
    ServiceScheduleSerializer,
    ScheduleRescheduleSerializer
)
from profiles.models import ClientProfile

# -------------------- Standard Services --------------------

class StandardServiceListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated | IsClient | IsLandscaper] 
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return ClientService.objects.filter(is_standard=True)


class StandardServiceCreateAPIView(CreateAPIView):
    permission_classes = [IsAdmin]  # Only admin can add standard services
    serializer_class = ServiceSerializer

    def perform_create(self, serializer):
        serializer.save(is_standard=True, landscaper=None)


class CustomServiceCreateAPIView(CreateAPIView):
    permission_classes = [IsLandscaper]
    serializer_class = ServiceSerializer

    def perform_create(self, serializer):
        landscaper = self.request.user.landscaper_profile
        name = serializer.validated_data.get("name")

        # Check if the service name already exists for this landscaper
        if Service.objects.filter(landscaper=landscaper, name=name).exists():
            raise ValidationError({"name": "You already have a service with this name."})

        serializer.save(is_standard=False, landscaper=landscaper)


# add ons
# services/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import AddOnService
from .serializers import AddOnServiceSerializer

# -----------------------------
# Client creates add-ons
# -----------------------------
class AddOnServiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # List only add-ons created by this client
        services = AddOnService.objects.filter(client=request.user).order_by("-created_at")
        serializer = AddOnServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddOnServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(client=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
# Admin delete any add-on
# -----------------------------
class AddOnServiceDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        service = get_object_or_404(AddOnService, pk=pk)
        service.delete()
        return Response({"detail": "Add-on deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# -----------------------------
# Landscaper gets add-ons of a client
# -----------------------------
class LandscaperClientAddOnsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        services = AddOnService.objects.filter(client_id=client_id).order_by("-created_at")
        serializer = AddOnServiceSerializer(services, many=True)
        return Response(serializer.data)

class LandscaperUpdateAddOnsAPIView(APIView):
    """
    PATCH: Update add-ons for a scheduled service
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, schedule_id):
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id)

        # Optional: restrict update to assigned landscaper
        if schedule.landscaper and schedule.landscaper.user != request.user:
            return Response(
                {"detail": "You are not allowed to update this schedule."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ServiceScheduleSerializer(
            schedule, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # Prepare response: show only add-ons with name, price, total
            add_ons = [
                {"id": a.id, "name": a.name, "price": float(a.price)}
                for a in schedule.add_ons.all()
            ]

            total_add_ons = sum(a["price"] for a in add_ons)

            return Response({
                "message": "Add-ons updated successfully",
                "add_ons": add_ons,
                "total_add_ons": total_add_ons
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------- Client Services --------------------

class ClientServicePreferenceAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsClient]

    def get_object(self):
        try:
            client_profile = ClientProfile.objects.get(user=self.request.user)
        except ClientProfile.DoesNotExist:
            raise NotFound("Client profile not found")

        preference, _ = ClientServicePreference.objects.get_or_create(
            client=client_profile
        )
        return preference

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClientServicePreferenceReadSerializer
        return ClientServicePreferenceWriteSerializer



class ClientPreferenceNoteUpdateAPIView(APIView):
    permission_classes = [IsClient]

    def post(self, request):
        client = request.user.clientprofile
        preference, _ = ClientServicePreference.objects.get_or_create(client=client)

        note = request.data.get("note", "")
        preference.note = note
        preference.save(update_fields=["note"])

        serializer = ClientServicePreferenceReadSerializer(preference)
        return Response(serializer.data)



class ClientServiceOverviewAPIView(APIView):
    permission_classes = [IsClient]  # Only client can view their service overview

    def get(self, request):
        client_profile = request.user.clientprofile
        preference, _ = ClientServicePreference.objects.get_or_create(client=client_profile)
        serializer = ClientServicePreferenceReadSerializer(preference)

        return Response({"service_overview": serializer.data})


# -------------------- Job / Schedule --------------------
# this is optional for job updated

class LandscaperCompleteJobAPIView(APIView):
    permission_classes = [IsLandscaper]

    def patch(self, request, id):
        schedule = get_object_or_404(
            ServiceSchedule,
            id=id,
            landscaper=request.user.landscaperprofilies
        )

        if schedule.is_completed:
            return Response({"detail": "Job already completed"}, status=400)

        service_ids = request.data.getlist("service_ids")
        note = request.data.get("note", "")

        services = ClientService.objects.filter(
            id__in=service_ids,
            is_standard=True,
            landscaper=request.user.landscaperprofilies
        )

        if not services.exists():
            return Response({"detail": "No valid services selected"}, status=400)

        total_price = sum(s.price for s in services if s.price)

        schedule.is_completed = True
        schedule.completed_at = now()
        schedule.completion_note = note
        schedule.price = total_price
        schedule.save()

        schedule.completed_services.set(services)

        # Save images
        for img in request.FILES.getlist("images"):
            ScheduleCompletionImage.objects.create(schedule=schedule, image=img)

        return Response({
            "job_id": schedule.id,
            "completed_services": [
                {"id": s.id, "name": s.name, "price": s.price} for s in services
            ],
            "total_price": total_price
        })




# class ClientJobHistoryAPIView(APIView):
#     permission_classes = [IsClient]  # Only client can view their completed jobs

#     def get(self, request):
#         client = request.user.clientprofile
#         jobs = ServiceSchedule.objects.filter(client=client, is_completed=True).order_by("-completed_at")
#         serializer = ServiceScheduleSerializer(jobs, many=True)
#         return Response(serializer.data)



class ClientJobHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client_profile = request.user.clientprofile

        # Get all completed jobs for the client
        jobs = (
            ServiceSchedule.objects
            .filter(client=client_profile, is_completed=True)
            .select_related("service", "landscaper", "client")
            .prefetch_related("completed_services", "images")
            .order_by("-completed_at")
        )

        serializer = ServiceScheduleSerializer(jobs, many=True)
        return Response(serializer.data, status=200)





class RescheduleServiceAPIView(APIView):
    permission_classes = [IsClient | IsLandscaper]  

    def patch(self, request, schedule_id):
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id)

        if (
            request.user.clientprofile != schedule.client and
            request.user.landscaper_profile != schedule.landscaper
        ):
            return Response({"detail": "Not allowed"}, status=403)

        serializer = ScheduleRescheduleSerializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Schedule rescheduled successfully",
            "new_date": serializer.data["scheduled_date"],
            "new_time": serializer.data["scheduled_time"]
        })


# property overview 
from property.models import Property
from .serializers import ServiceOverviewSerializer
class ServiceOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client_profile = getattr(request.user, "clientprofile", None)

        if not client_profile:
            return Response({"detail": "Client profile not found"}, status=400)

        preference = ClientServicePreference.objects.filter(
            client=client_profile
        ).prefetch_related("services").first()

        if not preference:
            return Response({"detail": "Service preference not set"}, status=200)

        last_service = ServiceSchedule.objects.filter(
            client=client_profile,
            is_completed=True
        ).order_by("-scheduled_date").first()

        next_service = ServiceSchedule.objects.filter(
            client=client_profile,
            is_completed=False
        ).order_by("scheduled_date").first()

        data = {
            "frequency": preference.frequency,
            "last_service_date": last_service.scheduled_date if last_service else None,
            "next_service_date": next_service.scheduled_date if next_service else None,
            "next_payment_date": next_service.scheduled_date if next_service else None,
            "services": preference.services.all()
        }

        serializer = ServiceOverviewSerializer(
            data,
            context={"client_profile": client_profile}
        )
        return Response(serializer.data)



# job list complete
class CompletedJobsAPIView(APIView):
    permission_classes = [IsLandscaper]

    def get(self, request):
        # Get the landscaper profile
        landscaper_profile = getattr(request.user, "landscaperprofilies", None)
        if not landscaper_profile:
            return Response({"completed_jobs": []})

        # Fetch all completed jobs for this landscaper
        completed_jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper_profile,
            is_completed=True
        ).order_by("-completed_at")

        jobs_list = []
        for job in completed_jobs:
            client_user = job.client.user
            landscaper_user = job.landscaper.user if job.landscaper else None

            # Completion images
            images = ScheduleCompletionImage.objects.filter(schedule=job)

            jobs_list.append({
                "job_id": job.id,
                "client": {
                    "id": client_user.id,
                    "name": getattr(client_user, "name", ""),
                    "email": client_user.email
                },
                "landscaper": {
                    "id": landscaper_user.id if landscaper_user else None,
                    "name": getattr(landscaper_user, "name", "") if landscaper_user else None,
                    "email": landscaper_user.email if landscaper_user else None
                },
                "services": [
                    {
                        "id": job.service.id,
                        "name": job.service.name,
                        "price": job.service.price
                    }
                ],
                "total_price": getattr(job.service, "price", 0),
                "note": job.completion_note,
                "completed_at": job.completed_at,
                "images": [img.image.url for img in images]
            })

        return Response({"completed_jobs": jobs_list})



class ServiceScheduleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schedule_id):
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id)

        serializer = ServiceScheduleSerializer(schedule)
        return Response({
            "id": schedule.id,
            "is_completed": schedule.is_completed,
            "schedule": serializer.data
        })




# from django.utils import timezone
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from services.models import ServiceSchedule
# from profiles.models import ClientProfile, LandscaperProfilies

# class RecentCompletedJobsAPIView(APIView):
    # """
    # Return the most recent completed job for the logged-in user.
    # Includes job info, completed services, total price, client/landscaper email,
    # time since completion, and the name/email of who completed it.
    # """
    # permission_classes = [IsAuthenticated]

    # def get(self, request):
    #     user = request.user

    #     # Determine role and fetch recent completed job
    #     if hasattr(user, "landscaperprofilies"):
    #         profile = user.landscaperprofilies
    #         job = ServiceSchedule.objects.filter(
    #             landscaper=profile,
    #             is_completed=True
    #         ).order_by("-completed_at").first()
    #     elif hasattr(user, "clientprofile"):
    #         profile = user.clientprofile
    #         job = ServiceSchedule.objects.filter(
    #             client=profile,
    #             is_completed=True
    #         ).order_by("-completed_at").first()
    #     else:
    #         return Response({"detail": "User profile not found."}, status=400)

    #     if not job:
    #         return Response({"detail": "No completed jobs found."}, status=200)

    #     # Time since completion
    #     now = timezone.now()
    #     diff = now - job.completed_at if job.completed_at else None
    #     if diff:
    #         if diff.days > 0:
    #             time_since = f"{diff.days} days ago"
    #         elif diff.seconds >= 3600:
    #             time_since = f"{diff.seconds // 3600} hours ago"
    #         elif diff.seconds >= 60:
    #             time_since = f"{diff.seconds // 60} minutes ago"
    #         else:
    #             time_since = "Just now"
    #     else:
    #         time_since = "N/A"

    #     # Completed services
    #     services = job.completed_services.all()
    #     services_data = [{"id": s.id, "name": s.name, "price": s.price} for s in services]
    #     total_price = sum(s.price for s in services)

    #     # Dynamic message
    #     service_names = ", ".join([s.name for s in services]) if services else job.service.name
    #     message = f"{service_names} completed successfully!"

    #     # Opposite party email (client if landscaper, landscaper if client)
    #     if hasattr(user, "landscaperprofilies"):
    #         opposite_email = job.client.user.email
    #     else:
    #         opposite_email = job.landscaper.user.email if job.landscaper else None

    #     # Completed by info
    #     if job.landscaper:
    #         completed_by_name = job.landscaper.user.name
    #         completed_by_email = job.landscaper.user.email
    #     else:
    #         completed_by_name = job.client.user.name
    #         completed_by_email = job.client.user.email

    #     return Response({
    #         "job": {
    #             "job_id": job.id,
    #             "scheduled_date": job.scheduled_date,
    #             "scheduled_time": job.scheduled_time,
    #             "time_since_completion": time_since,
    #             "total_price": total_price,
    #             "services": services_data,
    #             "opposite_email": opposite_email,
    #             "completed_by": {
    #                 "name": completed_by_name,
    #                 "email": completed_by_email
    #             },
    #             "message": message
    #         }
    #     })

    # 
# recent activity

class RecentActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get("limit", 10))

        # ------------------------------
        # Payments
        # ------------------------------
        payments_qs = ServiceSchedule.objects.filter(payment_status=PaymentStatus.PAID)
        if hasattr(user, "clientprofile"):
            payments_qs = payments_qs.filter(client=user.clientprofile)
        elif hasattr(user, "landscaperprofilies"):
            payments_qs = payments_qs.filter(landscaper=user.landscaperprofilies)
        payments_qs = payments_qs.order_by("-scheduled_date", "-scheduled_time")[:limit]

        payments_data = []
        for schedule in payments_qs:
            client_profile = getattr(schedule.client, "image", None)
            profile_image = client_profile.url if client_profile else None
            serialized = PaymentHistorySerializer(schedule, context={"request": request}).data
            serialized["client_profile_image"] = profile_image
            payments_data.append(serialized)

        # ------------------------------
        # Completed Jobs
        # ------------------------------
        completed_qs = ServiceSchedule.objects.filter(is_completed=True)
        if hasattr(user, "clientprofile"):
            completed_qs = completed_qs.filter(client=user.clientprofile)
        elif hasattr(user, "landscaperprofilies"):
            completed_qs = completed_qs.filter(landscaper=user.landscaperprofilies)
        completed_qs = completed_qs.order_by("-completed_at")[:limit]

        completed_data = []
        for job in completed_qs:
            client_profile = getattr(job.client, "image", None)
            profile_image = client_profile.url if client_profile else None
            completed_data.append({
                "job_id": job.id,
                "service": job.service.name,
                "scheduled_date": job.scheduled_date,
                "completed_at": job.completed_at,
                "client_name": getattr(job.client, "name", ""),
                "client_profile_image": profile_image
            })

        # ------------------------------
        # Rescheduled jobs
        # Using scheduled_date > created_at as approximate "reschedule"
        # ------------------------------
        rescheduled_qs = ServiceSchedule.objects.filter(
            scheduled_date__gt=F('created_at')
        )
        if hasattr(user, "clientprofile"):
            rescheduled_qs = rescheduled_qs.filter(client=user.clientprofile)
        elif hasattr(user, "landscaperprofilies"):
            rescheduled_qs = rescheduled_qs.filter(landscaper=user.landscaperprofilies)
        rescheduled_qs = rescheduled_qs.order_by("-scheduled_date")[:limit]

        rescheduled_data = []
        for job in rescheduled_qs:
            client_profile = getattr(job.client, "image", None)
            profile_image = client_profile.url if client_profile else None
            rescheduled_data.append({
                "job_id": job.id,
                "service": job.service.name,
                "scheduled_date": job.scheduled_date,
                "client_name": getattr(job.client, "name", ""),
                "client_profile_image": profile_image
            })

        return Response({
            "recent_payments": payments_data,
            "recent_completed_jobs": completed_data,
            "recent_rescheduled_jobs": rescheduled_data
        })