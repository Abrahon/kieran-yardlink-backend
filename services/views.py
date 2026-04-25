
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
from landscapers.models import WorkingHours, BusinessProfile, Service
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.utils import timezone
from accounts.models import User
from payments.serializers import PaymentHistorySerializer
from rest_framework import generics, status
from .models import ClientService, ClientServicePreference
from jobs.models import Job
from bookings.models import BookingRequest

from .serializers import (
    ServiceSerializer,
    ClientServicePreferenceWriteSerializer,
    ClientServicePreferenceReadSerializer,

)
from profiles.models import ClientProfile


# add ons
# services/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404





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

        serializer = JobSerializer(
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



# class ClientServiceOverviewAPIView(APIView):
#     permission_classes = [IsClient]  # Only client can view their service overview

#     def get(self, request):
#         client_profile = request.user.clientprofile
#         preference, _ = ClientServicePreference.objects.get_or_create(client=client_profile)
#         serializer = ClientServicePreferenceReadSerializer(preference)

#         return Response({"service_overview": serializer.data})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class ClientServiceOverviewAPIView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        client = request.user.clientprofile

        # -------------------------
        # GET ALL CLIENT JOBS
        # -------------------------
        jobs = Job.objects.filter(
            client=client
        ).select_related(
            "job_property",
            "invoice"
        ).order_by("-scheduled_date")

        if not jobs.exists():
            return Response({
                "message": "No service history found.",
                "data": None
            })

        last_job = jobs.first()

        # -------------------------
        # PROPERTY INFO
        # -------------------------
        property_obj = last_job.job_property

        property_data = None
        if property_obj:
            property_data = {
                "address": getattr(property_obj, "address", None),
                "property_size": getattr(property_obj, "property_size", None),
                "latitude": getattr(property_obj, "latitude", None),
                "longitude": getattr(property_obj, "longitude", None),
            }

        # -------------------------
        # LAST SERVICE INFO
        # -------------------------
        last_service_date = last_job.completed_at or last_job.scheduled_date

        # -------------------------
        # PAYMENT INFO
        # -------------------------
        last_invoice = getattr(last_job, "invoice", None)

        payment_data = None
        next_payment_due = None

        if last_invoice:
            payment_data = {
                "invoice_id": last_invoice.id,
                "invoice_number": last_invoice.invoice_number,
                "status": last_invoice.status,
                "total": last_invoice.total,
                "paid_at": last_invoice.paid_at,
                "checkout_url": last_invoice.stripe_checkout_url,
            }

            # next payment logic
            if last_invoice.status != "paid":
                next_payment_due = {
                    "amount": last_invoice.total,
                    "due_status": "pending",
                    "pay_url": last_invoice.stripe_checkout_url,
                }

        # -------------------------
        # SERVICE FREQUENCY (ESTIMATED)
        # -------------------------
        service_frequency = self.calculate_frequency(jobs)

        return Response({
            "property": property_data,
            "service_summary": {
                "total_jobs": jobs.count(),
                "last_service_date": last_service_date,
                "service_frequency": service_frequency,
                "last_job_status": last_job.status,
            },
            "payment": payment_data,
            "next_payment": next_payment_due,
        })

    # -------------------------
    # SIMPLE FREQUENCY LOGIC
    # -------------------------
    def calculate_frequency(self, jobs):
        if jobs.count() < 2:
            return "Not enough data"

        dates = list(
            jobs.values_list("scheduled_date", flat=True).order_by("-scheduled_date")[:5]
        )

        if len(dates) < 2:
            return "Not enough data"

        gaps = []
        for i in range(len(dates) - 1):
            gap = (dates[i] - dates[i + 1]).days
            gaps.append(gap)

        avg_gap = sum(gaps) / len(gaps)

        if avg_gap <= 7:
            return "Weekly"
        elif avg_gap <= 14:
            return "Bi-weekly"
        elif avg_gap <= 30:
            return "Monthly"
        else:
            return "Occasional"


# -------------------- Job / Schedule --------------------
# this is optional for job updated

class LandscaperCompleteJobAPIView(APIView):
    permission_classes = [IsLandscaper]

    def patch(self, request, id):
        schedule = get_object_or_404(
           Job,
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




class ClientJobHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client_profile = request.user.clientprofile

        # Get all completed jobs for the client
        jobs = (
            Job.objects
            .filter(client=client_profile, is_completed=True)
            .select_related("service", "landscaper", "client")
            .prefetch_related("completed_services", "images")
            .order_by("-completed_at")
        )

        serializer =JobSerializer(jobs, many=True)
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


# class ServiceOverviewAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         client_profile = getattr(request.user, "clientprofile", None)

#         if not client_profile:
#             return Response({"detail": "Client profile not found"}, status=400)

#         preference = ClientServicePreference.objects.filter(
#             client=client_profile
#         ).prefetch_related("services").first()

#         if not preference:
#             return Response({"detail": "Service preference not set"}, status=200)

#         last_service =Job.objects.filter(
#             client=client_profile,
#             is_completed=True
#         ).order_by("-scheduled_date").first()

#         next_service =Job.objects.filter(
#             client=client_profile,
#             is_completed=False
#         ).order_by("scheduled_date").first()

#         data = {
#             "frequency": preference.frequency,
#             "last_service_date": last_service.scheduled_date if last_service else None,
#             "next_service_date": next_service.scheduled_date if next_service else None,
#             "next_payment_date": next_service.scheduled_date if next_service else None,
#             "services": preference.services.all()
#         }

#         serializer = ServiceOverviewSerializer(
#             data,
#             context={"client_profile": client_profile}
#         )
#         return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone


class ServiceOverviewAPIView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        client = request.user.clientprofile

        # -----------------------------------
        # BOOKINGS (SOURCE OF TRUTH)
        # -----------------------------------
        bookings = BookingRequest.objects.filter(
            client=client
        ).select_related(
            "property",
            "service",
            "landscaper"
        ).order_by("-created_at")

        if not bookings.exists():
            return Response({
                "message": "No booking history found",
                "data": None
            })

        last_booking = bookings.first()

        # -----------------------------------
        # PROPERTY INFO
        # -----------------------------------
        property_obj = last_booking.property

        property_data = None
        if property_obj:
            property_data = {
                "id": property_obj.id,
                "address": getattr(property_obj, "address", None),
                "property_size": getattr(property_obj, "property_size", None),
                "latitude": getattr(property_obj, "latitude", None),
                "longitude": getattr(property_obj, "longitude", None),
            }

        # -----------------------------------
        # LAST SERVICE DATE
        # -----------------------------------
        last_service_date = last_booking.scheduled_date or last_booking.created_at.date()

        # -----------------------------------
        # NEXT UPCOMING BOOKING
        # -----------------------------------
        next_booking = bookings.filter(
            status__in=[
                BookingRequest.Status.PENDING,
                BookingRequest.Status.ACCEPTED,
                BookingRequest.Status.CONFIRMED
            ],
            scheduled_date__gte=timezone.now().date()
        ).order_by("scheduled_date").first()

        # -----------------------------------
        # COMPLETED JOBS COUNT
        # -----------------------------------
        completed_count = bookings.filter(
            status=BookingRequest.Status.COMPLETED
        ).count()

        # -----------------------------------
        # SERVICE FREQUENCY (REAL LOGIC)
        # -----------------------------------
        service_frequency = self.get_frequency(bookings)

        # -----------------------------------
        # LAST SERVICE DETAIL
        # -----------------------------------
        last_service = {
            "service_name": last_booking.service.name if last_booking.service else "Custom Service",
            "booking_type": last_booking.booking_type,
            "status": last_booking.status,
            "date": last_service_date
        }

        # -----------------------------------
        # NEXT PAYMENT (BASIC LOGIC)
        # -----------------------------------
        next_payment = None

        if next_booking and next_booking.price:
            next_payment = {
                "amount": next_booking.price,
                "scheduled_date": next_booking.scheduled_date,
                "status": next_booking.status,
            }

        return Response({
            "property": property_data,

            "service_summary": {
                "total_bookings": bookings.count(),
                "completed_services": completed_count,
                "last_service": last_service,
                "service_frequency": service_frequency,
            },

            "next_service": {
                "booking_id": next_booking.id if next_booking else None,
                "service_name": next_booking.service.name if next_booking and next_booking.service else None,
                "date": next_booking.scheduled_date if next_booking else None,
                "status": next_booking.status if next_booking else None,
            },

            "next_payment": next_payment
        })

    # -----------------------------------
    # SMART FREQUENCY CALCULATION
    # -----------------------------------
    def get_frequency(self, bookings):
        completed = bookings.filter(
            status=BookingRequest.Status.COMPLETED,
            scheduled_date__isnull=False
        ).order_by("-scheduled_date")[:6]

        dates = list(completed.values_list("scheduled_date", flat=True))

        if len(dates) < 2:
            return "Not enough data"

        gaps = []
        for i in range(len(dates) - 1):
            gap = (dates[i] - dates[i + 1]).days
            gaps.append(abs(gap))

        avg_gap = sum(gaps) / len(gaps)

        if avg_gap <= 7:
            return "Weekly"
        elif avg_gap <= 14:
            return "Bi-weekly"
        elif avg_gap <= 30:
            return "Monthly"
        else:
            return "Occasional"


# job list complete
# class CompletedJobsAPIView(APIView):
#     permission_classes = [IsLandscaper]

#     def get(self, request):
#         # Get the landscaper profile
#         landscaper_profile = getattr(request.user, "landscaperprofilies", None)
#         if not landscaper_profile:
#             return Response({"completed_jobs": []})

#         # Fetch all completed jobs for this landscaper
#         completed_jobs =Job.objects.filter(
#             landscaper=landscaper_profile,
#             is_completed=True
#         ).order_by("-completed_at")

#         jobs_list = []
#         for job in completed_jobs:
#             client_user = job.client.user
#             landscaper_user = job.landscaper.user if job.landscaper else None

#             # Completion images
#             images = ScheduleCompletionImage.objects.filter(schedule=job)

#             jobs_list.append({
#                 "job_id": job.id,
#                 "client": {
#                     "id": client_user.id,
#                     "name": getattr(client_user, "name", ""),
#                     "email": client_user.email
#                 },
#                 "landscaper": {
#                     "id": landscaper_user.id if landscaper_user else None,
#                     "name": getattr(landscaper_user, "name", "") if landscaper_user else None,
#                     "email": landscaper_user.email if landscaper_user else None
#                 },
#                 "services": [
#                     {
#                         "id": job.service.id,
#                         "name": job.service.name,
#                         "price": job.service.price
#                     }
#                 ],
#                 "total_price": getattr(job.service, "price", 0),
#                 "note": job.completion_note,
#                 "completed_at": job.completed_at,
#                 "images": [img.image.url for img in images]
#             })

#         return Response({"completed_jobs": jobs_list})




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from django.utils import timezone

class RecentActivityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get("limit", 10))

        # Detect role
        client = getattr(user, "clientprofile", None)
        landscaper = getattr(user, "landscaper_profile", None)

        # ------------------------------
        # BASE QUERY
        # ------------------------------
        jobs = Job.objects.select_related(
            "client__user",
            "external_client",
            "landscaper"
        )

        if client:
            jobs = jobs.filter(client=client)
        elif landscaper:
            jobs = jobs.filter(landscaper=landscaper)
        else:
            return Response({
                "recent_payments": [],
                "recent_completed_jobs": [],
                "recent_rescheduled_jobs": []
            })

        # ------------------------------
        # 1. RECENT PAYMENTS
        # ------------------------------
        payments_qs = jobs.filter(
            payment_status=Job.PaymentStatus.PAID
        ).order_by("-updated_at")[:limit]

        payments_data = [
            self.format_job(job, type="payment")
            for job in payments_qs
        ]

        # ------------------------------
        # 2. COMPLETED JOBS
        # ------------------------------
        completed_qs = jobs.filter(
            status=Job.Status.COMPLETED
        ).order_by("-completed_at")[:limit]

        completed_data = [
            self.format_job(job, type="completed")
            for job in completed_qs
        ]

        # ------------------------------
        # 3. RESCHEDULED JOBS
        # ------------------------------
        rescheduled_qs = jobs.filter(
            status=Job.Status.RESCHEDULED
        ).order_by("-updated_at")[:limit]

        rescheduled_data = [
            self.format_job(job, type="rescheduled")
            for job in rescheduled_qs
        ]

        return Response({
            "recent_payments": payments_data,
            "recent_completed_jobs": completed_data,
            "recent_rescheduled_jobs": rescheduled_data
        })

    # =====================================================
    # COMMON FORMATTER (VERY IMPORTANT)
    # =====================================================
    def format_job(self, job, type=""):
        client_name = job.client_name
        client_email = job.client_email

        # profile image
        profile_image = None
        if job.client and getattr(job.client, "image", None):
            profile_image = job.client.image.url

        return {
            "job_id": job.id,
            "type": type,
            "status": job.status,
            "payment_status": job.payment_status,

            "client_name": client_name,
            "client_email": client_email,
            "client_profile_image": profile_image,

            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,
            "completed_at": job.completed_at,

            "total_price": job.total_price,
        }