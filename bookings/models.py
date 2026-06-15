# bookings/models.py
from django.db import models
from django.utils import timezone
from accounts.models import User
from landscapers.models import BusinessProfile
from services.models import ClientService

# updated booking request
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError  # NEW

# Forward references to your existing models
from landscapers.models import Service, Addon, BusinessProfile
from profiles.models import ClientProfile
from property.models import Property


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
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="service_bookings"
    )

    service = models.ForeignKey(
        ClientService,
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
    scheduled_time = models.TimeField(null=True, blank=True)  

    scheduled_date = models.DateField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)

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



class BookingRequest(models.Model):

    class BookingType(models.TextChoices):
        ONE_TIME = "one_time", "One-Time"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Biweekly"
        MONTHLY = "monthly", "Monthly"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"     
        CONFIRMED = "confirmed", "Confirmed"  
        DECLINED = "declined", "Declined"
        COMPLETED = "completed", "Completed"

    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True
    )

    # Optional if booking is for a standard service
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    # Custom service description (if service is None)
    description = models.TextField(
        blank=True,
        null=True
    )

    # Booking type
    booking_type = models.CharField(
        max_length=10,
        choices=BookingType.choices,
        default=BookingType.ONE_TIME
    )

    # Recurrence
    recurring_day_of_week = models.CharField(
        max_length=10,
        choices=[
            ("MONDAY", "Monday"),
            ("TUESDAY", "Tuesday"),
            ("WEDNESDAY", "Wednesday"),
            ("THURSDAY", "Thursday"),
            ("FRIDAY", "Friday"),
            ("SATURDAY", "Saturday"),
            ("SUNDAY", "Sunday")
        ],
        null=True,
        blank=True,
        help_text="Used for recurring bookings"
    )

    # Date/time
    scheduled_date = models.DateField(
        null=True,
        blank=True
    )

    scheduled_time = models.TimeField(
        null=True,
        blank=True
    )

    # Add-ons
    addons = models.ManyToManyField(
        Addon,
        blank=True,
        related_name="bookings"
    )

    # Price (landscaper sets for request/custom)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )

    # Assigned landscaper
    landscaper = models.ForeignKey(
        BusinessProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bookings"
    )

    # Booking status
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Client note
    note = models.TextField(
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    # NEW ⭐ helps track job creation
    job_created = models.BooleanField(
        default=False
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["landscaper"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_date"]),
        ]

    def clean(self):

        # CUSTOM SERVICE VALIDATION
        if self.booking_type == self.BookingType.CUSTOM:
            if not self.description:
                raise ValidationError("Custom bookings must include a description.")
            if self.service:
                raise ValidationError("Custom booking should not have a standard service.")  # NEW


        # RECURRING VALIDATION
        if self.booking_type in [self.BookingType.WEEKLY, self.BookingType.BIWEEKLY]:
            if not self.recurring_day_of_week:
                raise ValidationError("Recurring bookings must have a day of the week selected.")


        # ONE TIME VALIDATION
        if self.booking_type == self.BookingType.ONE_TIME:
            if not self.scheduled_date or not self.scheduled_time:
                raise ValidationError("One-time bookings must have date and time set.")


        # FIXED SERVICE VALIDATION
        if self.service and self.service.pricing_type == Service.PricingType.FIXED:

            # price auto handled by system
            if self.price and self.price != self.service.base_price:
                raise ValidationError(
                    "Price cannot differ from fixed service price."
                )


        # REQUEST SERVICE VALIDATION
        if self.service and self.service.pricing_type == Service.PricingType.REQUEST:

            if self.price and self.price < self.service.min_price:
                raise ValidationError(
                    f"Price cannot be below minimum price {self.service.min_price}"
                )

    def is_custom_service(self):   # NEW
        return self.booking_type == self.BookingType.CUSTOM

    def is_price_required(self):   # NEW
        """
        Returns True if landscaper must set price
        """
        if self.booking_type == self.BookingType.CUSTOM:
            return True

        if self.service and self.service.pricing_type == Service.PricingType.REQUEST:
            return True

        return False

    def __str__(self):

        if self.service:
            return f"{self.client.user.email} - {self.service.name} ({self.status})"

        return f"{self.client.user.email} - Custom Service ({self.status})"


from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from bookings.models import BookingRequest
from landscapers.models import Service, Addon


class BookingRequestItem(models.Model):
    class ItemType(models.TextChoices):
        STANDARD_SERVICE = "standard_service", "Standard Service"
        ADDON = "addon", "Addon"
        CUSTOM = "custom", "Custom" 

    booking = models.ForeignKey(
        BookingRequest,
        on_delete=models.CASCADE,
        related_name="items"
    )

    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_items"
    )

    addon = models.ForeignKey(
        Addon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_items"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)]
    )

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def clean(self):
        if self.item_type == self.ItemType.STANDARD_SERVICE and not self.service:
            raise ValidationError("Standard service booking item must have a service.")
        if self.item_type == self.ItemType.ADDON and not self.addon:
            raise ValidationError("Addon booking item must have an addon.")
        if self.item_type == self.ItemType.CUSTOM and not self.name:
            raise ValidationError("Custom booking item must have a name.")

    def __str__(self):
        return f"Booking #{self.booking.id} - {self.name}"