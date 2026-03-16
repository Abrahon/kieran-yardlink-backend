from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from invoices.models import Invoice
from invoices.serializers import InvoiceSerializer
from invoices.services import create_invoice_from_completed_job
from invoices.utils import send_invoice_email
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

    # Plug your existing Stripe code here
    stripe_checkout_url = request.data.get("stripe_checkout_url")
    stripe_session_id = request.data.get("stripe_session_id")

    try:
        invoice = create_invoice_from_completed_job(
            job=job,
            created_by=request.user,
            stripe_checkout_url=stripe_checkout_url,
            stripe_session_id=stripe_session_id,
        )
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    serializer = InvoiceSerializer(invoice)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def send_job_invoice(request, invoice_id):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=status.HTTP_403_FORBIDDEN)

    try:
        invoice = Invoice.objects.get(
            id=invoice_id,
            job__landscaper=landscaper
        )
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

    frontend_invoice_url = request.data.get("frontend_invoice_url")

    try:
        send_invoice_email(invoice, frontend_invoice_url=frontend_invoice_url)
    except Exception as e:
        return Response({"error": f"Email send failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    invoice.status = Invoice.Status.SENT
    invoice.save(update_fields=["status", "updated_at"])

    return Response({
        "message": "Invoice sent successfully.",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "sent_to": invoice.sent_to_email,
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def mark_invoice_paid(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

    invoice.status = Invoice.Status.PAID
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=["status", "paid_at", "updated_at"])

    invoice.job.payment_status = Job.PaymentStatus.PAID
    invoice.job.save(update_fields=["payment_status", "updated_at"])

    return Response({
        "message": "Invoice marked as paid.",
        "invoice_id": invoice.id,
        "job_id": invoice.job.id,
        "payment_status": invoice.job.payment_status,
    }, status=status.HTTP_200_OK)