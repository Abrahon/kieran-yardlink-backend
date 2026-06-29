
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
from profiles.models import ClientProfile
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from property.models import Property
from invoice.models import Invoice
from jobs.serializers import JobSerializer






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




#             return "Occasional"

class ServiceOverviewAPIView(APIView):
    permission_classes = [IsClient]

    def get(self, request):

        # -------------------------
        # GET CLIENT PROFILE SAFELY
        # -------------------------
        client = ClientProfile.objects.filter(user=request.user).first()

        if not client:
            return Response({
                "detail": "Client profile not found."
            }, status=404)

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

        jobs = Job.objects.filter(
            client=client,
            is_active=True
        ).select_related(
            "job_property",
            "invoice"
        ).prefetch_related(
            "images"
        ).order_by("-scheduled_date")

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
        # PROPERTY INFO (ONLY ACTIVE)
        # -------------------------
        # -------------------------
        # PROPERTY INFO (FIXED)
        # -------------------------
        # -------------------------
        # PROPERTY INFO (ONLY ACTIVE PROPERTY)
        # -------------------------
        property_obj = Property.objects.filter(
            owner=client.user,
            is_active=True
        ).order_by("-created_at").first()

        property_data = None
        prop_instance = None

        if property_obj:
            prop_instance = property_obj

        property_data = None

        if property_obj:
            property_data = {
                "id": property_obj.id,
                "address": property_obj.address,
                "property_size": property_obj.property_size,
                "latitude": property_obj.latitude,
                "longitude": property_obj.longitude,
                "cut_height_inches": property_obj.cut_height_inches,
                "grass_types": property_obj.grass_types,
                "notes": property_obj.notes,
                "is_active": property_obj.is_active,
                "images": property_obj.images, 
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
