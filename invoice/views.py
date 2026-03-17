from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes


from invoice.models import Invoice
from invoice.serializers import InvoiceSerializer
from invoice.services import create_invoice_from_completed_job
from invoice.utils import send_invoice_email
from jobs.models import Job


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



from rest_framework.permissions import IsAuthenticated
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


from payments.stripe_service import create_invoice_checkout_session

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
    

from django.template.loader import get_template



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_job_invoice(request, invoice_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        invoice = Invoice.objects.get(
            id=invoice_id,
            job__landscaper=landscaper
        )
    except Invoice.DoesNotExist:
        return Response(
            {"error": "Invoice not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    frontend_invoice_url = request.data.get("frontend_invoice_url")

    try:
        get_template("emails/invoice_email.txt")
        get_template("emails/invoice_email.html")
        send_invoice_email(invoice, frontend_invoice_url=frontend_invoice_url)
    except Exception as e:
        return Response(
            {"error": f"Email send failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    invoice.status = Invoice.Status.SENT
    invoice.save(update_fields=["status", "updated_at"])

    return Response({
        "message": "Invoice sent successfully.",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "sent_to": invoice.sent_to_email,
        "stripe_checkout_url": invoice.stripe_checkout_url,
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