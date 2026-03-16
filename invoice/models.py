from django.db import models

# Create your models here.
from decimal import Decimal
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from jobs.models import Job


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="invoice"
    )

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    issued_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)]
    )

    notes = models.TextField(blank=True, null=True)

    # Stripe fields
    stripe_checkout_url = models.URLField(max_length=1000, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    sent_to_email = models.EmailField(blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_invoices"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} - Job #{self.job_id}"

    @staticmethod
    def generate_invoice_number():
        return f"INV-{uuid4().hex[:10].upper()}"




class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="line_items"
    )

    item_type = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)]
    )

    source_job_item_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} - {self.invoice.invoice_number}"