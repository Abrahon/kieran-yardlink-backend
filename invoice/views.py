from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from payments.stripe_service import create_invoice_checkout_session
from django.template.loader import get_template
from invoice.models import Invoice
from invoice.serializers import InvoiceSerializer
from invoice.services import create_invoice_from_completed_job
from invoice.utils import send_invoice_email
from jobs.models import Job
from landscapers.models import BusinessProfile
from rest_framework.permissions import IsAuthenticated

class ClientInvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return Invoice.objects.none()

        return Invoice.objects.filter(job__client=client).order_by("-created_at")


class ClientInvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        client = getattr(self.request.user, "clientprofile", None)
        if not client:
            return Invoice.objects.none()

        return Invoice.objects.filter(job__client=client)





@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_job_invoice(request, job_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

    try:
        job = Job.objects.get(
            id=job_id,
            landscaper=landscaper,
            status=Job.Status.COMPLETED,
            is_active=True
        )
    except Job.DoesNotExist:
        return Response({"error": "Completed job not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        invoice = create_invoice_from_completed_job(job=job, created_by=request.user)
    except Exception as e:
        return Response({"error": f"Invoice creation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)






@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def regenerate_invoice_checkout(request, invoice_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

    try:
        invoice = Invoice.objects.get(id=invoice_id, job__landscaper=landscaper)
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        session = create_invoice_checkout_session(invoice)
        invoice.stripe_checkout_url = session.url
        invoice.stripe_session_id = session.id
        if invoice.status in [Invoice.Status.DRAFT, Invoice.Status.SENT]:
            invoice.status = Invoice.Status.PENDING
        invoice.save(update_fields=[
            "stripe_checkout_url",
            "stripe_session_id",
            "status",
            "updated_at",
        ])
    except Exception as e:
        return Response({"error": f"Stripe checkout regeneration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Stripe checkout generated successfully.",
        "invoice_id": invoice.id,
        "stripe_checkout_url": invoice.stripe_checkout_url,
        "stripe_session_id": invoice.stripe_session_id,
    }, status=status.HTTP_200_OK)
    


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from invoice.models import Invoice
from django.shortcuts import get_object_or_404


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_job_invoice(request, invoice_id):

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    # ✅ STEP 1: GET INVOICE (NO FILTER FIRST)
    invoice = get_object_or_404(
        Invoice.objects.select_related("job", "job__landscaper"),
        id=invoice_id
    )

    # ❌ STEP 2: VERIFY OWNERSHIP PROPERLY
    if invoice.job.landscaper_id != landscaper.id:
        return Response(
            {
                "error": "Invoice does not belong to this landscaper.",
                "debug": {
                    "invoice_job_landscaper_id": invoice.job.landscaper_id,
                    "request_landscaper_id": landscaper.id
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # 🚨 Stripe setup
    import stripe
    from django.conf import settings

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # expire old session safely
    if invoice.stripe_session_id:
        try:
            stripe.checkout.Session.expire(invoice.stripe_session_id)
        except Exception:
            pass

    # create new session
    try:
        session = create_invoice_checkout_session(invoice)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # save invoice
    invoice.stripe_session_id = session.id
    invoice.stripe_checkout_url = session.url
    invoice.status = Invoice.Status.SENT
    invoice.save(update_fields=[
        "stripe_session_id",
        "stripe_checkout_url",
        "status",
        "updated_at"
    ])

    # send email
    try:
        send_invoice_email(
            invoice,
            frontend_invoice_url=request.data.get("frontend_invoice_url")
        )
    except Exception as e:
        return Response(
            {"error": f"Email send failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": "Invoice sent successfully.",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "sent_to": invoice.sent_to_email,
        "stripe_checkout_url": session.url,
    }, status=status.HTTP_200_OK)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_invoice_paid(request, invoice_id):
    landscaper = getattr(request.user, "landscaper_profile", None)

    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found"},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        invoice = Invoice.objects.select_related("job").get(
            id=invoice_id,
            job__landscaper=landscaper
        )
    except Invoice.DoesNotExist:
        return Response(
            {"error": "Invoice not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if invoice.status == Invoice.Status.PAID:
        return Response({
            "message": "Invoice already paid",
            "invoice_id": invoice.id
        })

    invoice.status = Invoice.Status.PAID
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=["status", "paid_at", "updated_at"])

    if invoice.job:
        invoice.job.payment_status = Job.PaymentStatus.PAID
        invoice.job.save(update_fields=["payment_status", "updated_at"])

    return Response({
        "message": "Invoice marked as paid",
        "invoice_id": invoice.id,
        "status": invoice.status,
        "paid_at": invoice.paid_at
    }, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoice.models import Invoice
from profiles.models import LandscaperProfilies


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_invoices(request):

    landscaper = LandscaperProfilies.objects.filter(user=request.user).first()

    if not landscaper:
        return Response({"error": "Landscaper not found"}, status=403)

    invoices = Invoice.objects.filter(
        job__landscaper_id=landscaper.id
    ).select_related("job")

    return Response({
        "count": invoices.count(),
        "results": [
            {
                "id": i.id,
                "job_id": i.job_id,
                "landscaper_id": i.job.landscaper_id
            }
            for i in invoices
        ]
    })