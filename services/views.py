
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from common.permissions import IsClient, IsAdmin, IsLandscaper
from rest_framework.exceptions import ValidationError

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



# -------------------- Client Services --------------------

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import NotFound

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
    permission_classes = [IsLandscaper] 

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


from rest_framework import generics, status

class LandscaperCompleteJobAPIView(generics.RetrieveUpdateAPIView):
    """
    GET  -> Retrieve job details for landscaper
    PATCH -> Update completed services, add note, upload images, calculate price
    """
    permission_classes = [IsLandscaper]
    lookup_field = "schedule_id"
    queryset = ServiceSchedule.objects.all()

    def get_serializer_class(self):
        return ScheduleCompletionSerializer

    def get_object(self):
        # Ensure only assigned landscaper can access
        schedule_id = self.kwargs.get("id")
        return get_object_or_404(
            ServiceSchedule,
            id=schedule_id,
            landscaper=self.request.user.landscaper_profile
        )

    def patch(self, request, *args, **kwargs):
        schedule = self.get_object()

        service_ids = request.data.get("service_ids", [])
        note = request.data.get("note", "")

        if not service_ids:
            return Response({"detail": "Please provide completed service IDs"}, status=400)

        completed_services = Service.objects.filter(
            id__in=service_ids,
            is_standard=True,
            landscaper=request.user.landscaper_profile
        )

        if not completed_services.exists():
            return Response({"detail": "No valid standard services selected"}, status=400)

        # Update schedule
        schedule.is_completed = True
        schedule.completed_at = now()
        schedule.note = note
        schedule.price = sum(s.price for s in completed_services)
        schedule.save(update_fields=["is_completed", "completed_at", "note", "price"])

        # Save images
        images_urls = []
        for img in request.FILES.getlist("images"):
            img_obj = ScheduleCompletionImage.objects.create(schedule=schedule, image=img)
            images_urls.append(img_obj.image.url)

        # Prepare response
        response_data = {
            "services": [{"id": s.id, "name": s.name, "price": s.price} for s in completed_services],
            "total_price": schedule.price,
            "images": images_urls,
            "note": note,
            "completed_at": schedule.completed_at
        }

        serializer = ScheduleCompletionSerializer(response_data)
        return Response(serializer.data)





class ClientJobHistoryAPIView(APIView):
    permission_classes = [IsClient]  # Only client can view their completed jobs

    def get(self, request):
        client = request.user.clientprofile
        jobs = ServiceSchedule.objects.filter(client=client, is_completed=True).order_by("-completed_at")
        serializer = ServiceScheduleSerializer(jobs, many=True)
        return Response(serializer.data)



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



class CompletedJobsAPIView(APIView):
    permission_classes = [IsLandscaper]

    def get(self, request):
        landscaper_profile = getattr(request.user, "landscaper_profile", None)
        if not landscaper_profile:
            return Response({"completed_jobs": []})

        completed_jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper_profile,
            is_completed=True
        ).order_by("-completed_at")

        jobs_list = []
        for job in completed_jobs:
            completed_services = Service.objects.filter(
                id__in=[s.id for s in job.services.all()],
                is_standard=True,
                landscaper=landscaper_profile
            )

            images = ScheduleCompletionImage.objects.filter(schedule=job)
            jobs_list.append({
                "job_id": job.id,
                "client": {
                    "id": job.client.user.id,
                    "name": getattr(job.client.user, "name", ""),
                    "email": job.client.user.email
                },
                "services": [{"id": s.id, "name": s.name, "price": s.price} for s in completed_services],
                "total_price": job.price,
                "note": job.note,
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

# complted job sse can clinet
# class LandscaperCompleteJobAPIView(generics.RetrieveUpdateAPIView):
#     permission_classes = [IsLandscaper]
#     lookup_field = "id"
#     queryset = ServiceSchedule.objects.all()

#     def get_object(self):
#         schedule_id = self.kwargs.get("id")
#         return get_object_or_404(
#             ServiceSchedule,
#             id=schedule_id,
#             landscaper=self.request.user.landscaper_profile
#         )

#     def get(self, request, *args, **kwargs):
#         schedule = self.get_object()
#         client = schedule.client

#         # Current job details
#         current_job_data = {
#             "id": schedule.id,
#             "services": [{"id": s.id, "name": s.name, "price": s.price} for s in schedule.services.all()],
#             "note": schedule.note,
#             "completed_at": schedule.completed_at,
#             "is_completed": schedule.is_completed
#         }

#         # All previously completed jobs for this client
#         completed_jobs = ServiceSchedule.objects.filter(
#             client=client,
#             is_completed=True
#         ).exclude(id=schedule.id).order_by("-completed_at")

#         completed_jobs_data = []
#         for job in completed_jobs:
#             completed_jobs_data.append({
#                 "id": job.id,
#                 "services": [{"id": s.id, "name": s.name, "price": s.price} for s in job.services.all()],
#                 "note": job.note,
#                 "completed_at": job.completed_at
#             })

#         return Response({
#             "current_job": current_job_data,
#             "completed_jobs": completed_jobs_data
#         })
