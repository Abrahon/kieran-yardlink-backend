# bookings/models.py
from django.db import models
from django.utils import timezone
from accounts.models import User
from landscapers.models import LandscaperProfile
from services.models import Service


class BookingStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    CASH_PENDING = "cash_pending", "Cash Pending"



class ServiceBooking(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_bookings"
    )

    landscaper = models.ForeignKey(
        LandscaperProfile,
        on_delete=models.CASCADE,
        related_name="service_bookings"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.REQUESTED
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("cash_pending", "Cash Pending"),
            ("paid", "Paid")
        ],
        default="pending"
    )

    scheduled_date = models.DateField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_completed(self):

        if self.status != BookingStatus.COMPLETED:
            self.status = BookingStatus.COMPLETED
            self.completed_at = timezone.now()
            # Optional: auto-update cash_pending
            if self.payment_status == PaymentStatus.CASH_PENDING:
                self.payment_status = PaymentStatus.PAID
                self.save(update_fields=["status", "completed_at", "payment_status"])
            else:
                self.save(update_fields=["status", "completed_at"])
