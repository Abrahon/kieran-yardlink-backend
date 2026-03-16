# from decimal import Decimal
# from django.db import transaction
# from django.utils import timezone
# from datetime import timedelta

# from invoice.models import Invoice, InvoiceLineItem
# from jobs.models import Job


# def create_invoice_from_completed_job(job: Job, created_by=None, stripe_checkout_url=None, stripe_session_id=None):
#     if job.status != Job.Status.COMPLETED:
#         raise ValueError("Invoice can only be created for a completed job.")

#     if hasattr(job, "invoice"):
#         return job.invoice

#     completed_items = job.items.filter(is_completed=True).order_by("sort_order", "id")
#     if not completed_items.exists():
#         raise ValueError("Cannot create invoice without completed items.")

#     with transaction.atomic():
#         invoice = Invoice.objects.create(
#             job=job,
#             invoice_number=Invoice.generate_invoice_number(),
#             status=Invoice.Status.PENDING,
#             due_at=timezone.now() + timedelta(days=7),
#             subtotal=Decimal("0.00"),
#             total=Decimal("0.00"),
#             sent_to_email=job.client.user.email if job.client and job.client.user else None,
#             created_by=created_by,
#             stripe_checkout_url=stripe_checkout_url,
#             stripe_session_id=stripe_session_id,
#         )

#         subtotal = Decimal("0.00")

#         for item in completed_items:
#             line_total = item.price or Decimal("0.00")

#             InvoiceLineItem.objects.create(
#                 invoice=invoice,
#                 item_type=item.item_type,
#                 name=item.name,
#                 description=item.description,
#                 unit_price=line_total,
#                 quantity=1,
#                 line_total=line_total,
#                 source_job_item_id=item.id,
#             )
#             subtotal += line_total

#         invoice.subtotal = subtotal
#         invoice.total = subtotal
#         invoice.save(update_fields=["subtotal", "total", "updated_at"])

#         return invoice

from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from invoice.models import Invoice, InvoiceLineItem
from jobs.models import Job
from payments.stripe_service import create_invoice_checkout_session


# def create_invoice_from_completed_job(job: Job, created_by=None):
#     if job.status != Job.Status.COMPLETED:
#         raise ValueError("Invoice can only be created for a completed job.")

#     if hasattr(job, "invoice"):
#         return job.invoice

#     completed_items = job.items.filter(is_completed=True).order_by("sort_order", "id")
#     if not completed_items.exists():
#         raise ValueError("Cannot create invoice without completed items.")

#     with transaction.atomic():
#         invoice = Invoice.objects.create(
#             job=job,
#             invoice_number=Invoice.generate_invoice_number(),
#             status=Invoice.Status.DRAFT,
#             due_at=timezone.now() + timedelta(days=7),
#             subtotal=Decimal("0.00"),
#             total=Decimal("0.00"),
#             sent_to_email=job.client.user.email if job.client and job.client.user else None,
#             created_by=created_by,
#         )

#         subtotal = Decimal("0.00")

#         for item in completed_items:
#             line_total = item.price or Decimal("0.00")

#             InvoiceLineItem.objects.create(
#                 invoice=invoice,
#                 item_type=item.item_type,
#                 name=item.name,
#                 description=item.description,
#                 unit_price=line_total,
#                 quantity=1,
#                 line_total=line_total,
#                 source_job_item_id=item.id,
#             )

#             subtotal += line_total

#         invoice.subtotal = subtotal
#         invoice.total = subtotal
#         invoice.save(update_fields=["subtotal", "total", "updated_at"])

#         # CREATE STRIPE CHECKOUT HERE
#         session = create_invoice_checkout_session(invoice)

#         invoice.stripe_checkout_url = session.url
#         invoice.stripe_session_id = session.id
#         invoice.status = Invoice.Status.PENDING
#         invoice.save(update_fields=[
#             "stripe_checkout_url",
#             "stripe_session_id",
#             "status",
#             "updated_at",
#         ])

#         return invoice




def create_invoice_from_completed_job(job: Job, created_by=None):
    if job.status != Job.Status.COMPLETED:
        raise ValueError("Invoice can only be created for a completed job.")

    # if invoice already exists, ensure stripe checkout exists
    existing_invoice = getattr(job, "invoice", None)
    if existing_invoice:
        if not existing_invoice.stripe_checkout_url or not existing_invoice.stripe_session_id:
            session = create_invoice_checkout_session(existing_invoice)
            existing_invoice.stripe_checkout_url = session.url
            existing_invoice.stripe_session_id = session.id

            if existing_invoice.status in [Invoice.Status.DRAFT, Invoice.Status.SENT]:
                existing_invoice.status = Invoice.Status.PENDING

            existing_invoice.save(update_fields=[
                "stripe_checkout_url",
                "stripe_session_id",
                "status",
                "updated_at",
            ])
        return existing_invoice

    completed_items = job.items.filter(is_completed=True).order_by("sort_order", "id")
    if not completed_items.exists():
        raise ValueError("Cannot create invoice without completed items.")

    with transaction.atomic():
        invoice = Invoice.objects.create(
            job=job,
            invoice_number=Invoice.generate_invoice_number(),
            status=Invoice.Status.DRAFT,
            due_at=timezone.now() + timedelta(days=7),
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            sent_to_email=job.client.user.email if job.client and job.client.user else None,
            created_by=created_by,
        )

        subtotal = Decimal("0.00")

        for item in completed_items:
            line_total = item.price or Decimal("0.00")

            InvoiceLineItem.objects.create(
                invoice=invoice,
                item_type=item.item_type,
                name=item.name,
                description=item.description,
                unit_price=line_total,
                quantity=1,
                line_total=line_total,
                source_job_item_id=item.id,
            )
            subtotal += line_total

        invoice.subtotal = subtotal
        invoice.total = subtotal
        invoice.save(update_fields=["subtotal", "total", "updated_at"])

        session = create_invoice_checkout_session(invoice)
        invoice.stripe_checkout_url = session.url
        invoice.stripe_session_id = session.id
        invoice.status = Invoice.Status.PENDING
        invoice.save(update_fields=[
            "stripe_checkout_url",
            "stripe_session_id",
            "status",
            "updated_at",
        ])

        return invoice