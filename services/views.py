
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from common.permissions import IsClient, IsAdmin, IsLandscaper
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from landscapers.models import WorkingHours, BusinessProfile, Service
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
from invoice.models import Invoice
from .serializers import (
    ServiceSerializer,
    ClientServicePreferenceWriteSerializer,
    ClientServicePreferenceReadSerializer,

)
from profiles.models import ClientProfile
from rest_framework.views import APIView
from django.db.models import Q
from jobs.models import Job, JobImage
from django.db.models import F
from django.utils import timezone
from payments.enums import PaymentStatus
# add ons
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
class ServiceOverviewAPIView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        client = request.user.clientprofile

        # -------------------------
        # ALL CLIENT JOBS
        # -------------------------
        jobs = Job.objects.filter(
            client=client,
            is_active=True
        ).select_related(
            "job_property",
            "invoice"
        ).prefetch_related(
            "images"
        ).order_by("-scheduled_date")

        if not jobs.exists():
            return Response({
                "message": "No service history found.",
                "data": None
            })

        # -------------------------
        # LAST COMPLETED JOB (FOR SERVICE)
        # -------------------------
        last_completed_job = jobs.filter(
            status=Job.Status.COMPLETED
        ).order_by("-completed_at").first()

        # -------------------------
        # LAST JOB WITH INVOICE (FOR PAYMENT)
        # -------------------------


        last_invoice = (
            Invoice.objects
            .filter(
                job__client=client,
                status__in=["pending", "unpaid", "sent", "draft"]
            )
            .select_related("job")
            .order_by("-created_at")
            .first()
        )

        # -------------------------
        # PROPERTY INFO
        # -------------------------
        property_obj = (
            Job.objects.filter(
                client=client,
                job_property__isnull=False,
            )
            .select_related("job_property")
            .order_by("-scheduled_date", "-scheduled_time")
            .first()
        )

        property_data = None

        if property_obj and property_obj.job_property:
            prop = property_obj.job_property

            property_data = {
                "id": prop.id,
                "address": getattr(prop, "address", None),
                "property_size": getattr(prop, "property_size", None),
                "latitude": getattr(prop, "latitude", None),
                "longitude": getattr(prop, "longitude", None),
                "is_active": prop.is_active,  
            }
        # -------------------------
        # SERVICE SUMMARY
        # -------------------------
        service_summary = {
            "total_jobs": jobs.count(),
            "last_service_date": (
                last_completed_job.completed_at if last_completed_job else None
            ),
            "service_frequency": self.calculate_frequency(jobs),
            "last_job_status": last_completed_job.status if last_completed_job else None,
        }

        # -------------------------
        # PAYMENT INFO
        # -------------------------
        payment_data = None
        next_payment_due = None

        if last_invoice and last_invoice.job:
            invoice = last_invoice

            payment_data = {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "status": invoice.status,
                "total": invoice.total,
                "paid_at": invoice.paid_at,
                "checkout_url": invoice.stripe_checkout_url,
            }

            if invoice.status != "paid":
                next_payment_due = {
                    "amount": invoice.total,
                    "status": invoice.status,
                    "pay_url": invoice.stripe_checkout_url,
                }

        # -------------------------
        # RECENT IMAGES
        # -------------------------
        recent_images = self.get_recent_images(jobs)

        return Response({
            "property": property_data,
            "service_summary": service_summary,
            "payment": payment_data,
            "next_payment": next_payment_due,
            "recent_images": recent_images
        })

    # -------------------------
    # RECENT IMAGES METHOD
    # -------------------------
    def get_recent_images(self, jobs):
        images = JobImage.objects.filter(
            job__in=jobs
        ).order_by("-created_at")[:10]

        return [
            {
                "id": img.id,
                "job_id": img.job_id,
                "image": img.image.url if img.image else None,
                "image_type": img.image_type,
                "caption": img.caption,
                "created_at": img.created_at,
            }
            for img in images
        ]

    # -------------------------
    # SERVICE FREQUENCY
    # -------------------------
    def calculate_frequency(self, jobs):
        if jobs.count() < 2:
            return "Not enough data"

        dates = list(
            jobs.values_list("scheduled_date", flat=True)
            .order_by("-scheduled_date")[:5]
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
            payment_status=PaymentStatus.PAID
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
