# bookings/models.py
from django.db import models
from django.utils import timezone
from accounts.models import User
from landscapers.models import BusinessProfile
from services.models import ClientService


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


# # updated booking request
# from django.db import models
# from django.conf import settings
# from django.core.validators import MinValueValidator
# from django.utils import timezone
# from decimal import Decimal

# # Forward references to your existing models
# from landscapers.models import Service, Addon, BusinessProfile
# from profiles.models import ClientProfile
# from property.models import Property


# class BookingRequest(models.Model):
#     class BookingType(models.TextChoices):
#         ONE_TIME = "one_time", "One-Time"
#         WEEKLY = "weekly", "Weekly"
#         BIWEEKLY = "biweekly", "Biweekly"
#         CUSTOM = "custom", "Custom"

#     class Status(models.TextChoices):
#         PENDING = "pending", "Pending"
#         ACCEPTED = "accepted", "Accepted"
#         CONFIRMED = "confirmed", "Confirmed"
#         DECLINED = "declined", "Declined"
#         COMPLETED = "completed", "Completed"

#     client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="bookings")
#     property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True)

#     # Optional if booking is for a standard service
#     service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")

#     # Custom service description (if service is None)
#     description = models.TextField(blank=True, null=True)

#     # Booking type
#     booking_type = models.CharField(
#         max_length=10,
#         choices=BookingType.choices,
#         default=BookingType.ONE_TIME
#     )

#     # Recurrence: only relevant if booking_type = weekly/biweekly
#     recurring_day_of_week = models.CharField(
#         max_length=10,
#         choices=[
#             ("MONDAY", "Monday"), ("TUESDAY", "Tuesday"), ("WEDNESDAY", "Wednesday"),
#             ("THURSDAY", "Thursday"), ("FRIDAY", "Friday"), ("SATURDAY", "Saturday"),
#             ("SUNDAY", "Sunday")
#         ],
#         null=True,
#         blank=True,
#         help_text="Used for recurring bookings"
#     )

#     # Date/time for one-time booking or start date for recurring
#     scheduled_date = models.DateField(null=True, blank=True)
#     scheduled_time = models.TimeField(null=True, blank=True)

#     # Add-ons
#     addons = models.ManyToManyField(Addon, blank=True, related_name="bookings")

#     # Price (set by landscaper for Price Upon Request or custom service)
#     price = models.DecimalField(
#         max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
#         null=True, blank=True
#     )

#     # Related landscaper (auto-set when accepted)
#     landscaper = models.ForeignKey(
#         BusinessProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_bookings"
#     )

#     # Booking status
#     status = models.CharField(
#         max_length=10,
#         choices=Status.choices,
#         default=Status.PENDING
#     )

#     # Client note
#     note = models.TextField(blank=True, null=True)

#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["-created_at"]
#         indexes = [
#             models.Index(fields=["client"]),
#             models.Index(fields=["landscaper"]),
#             models.Index(fields=["status"]),
#             models.Index(fields=["scheduled_date"]),
#         ]

#     def clean(self):
#         # Validation for booking type
#         if self.booking_type in [self.BookingType.WEEKLY, self.BookingType.BIWEEKLY] and not self.recurring_day_of_week:
#             raise ValidationError("Recurring bookings must have a day of the week selected.")

#         if self.booking_type == self.BookingType.ONE_TIME and (not self.scheduled_date or not self.scheduled_time):
#             raise ValidationError("One-time bookings must have date and time set.")

#         if self.booking_type == self.BookingType.CUSTOM and not self.description:
#             raise ValidationError("Custom bookings must include a description.")

#         # Price validation: if service has FIXED price, price must match
#         if self.service and self.service.pricing_type == Service.PricingType.FIXED:
#             if self.price is not None and self.price != self.service.base_price:
#                 raise ValidationError("Price cannot differ from fixed service price.")

#         # Price minimum for REQUEST type service
#         if self.service and self.service.pricing_type == Service.PricingType.REQUEST:
#             if self.price is not None and self.price < self.service.min_price:
#                 raise ValidationError(f"Price cannot be below the minimum of {self.service.min_price}.")

#     def __str__(self):
#         if self.service:
#             return f"{self.client.user.email} - {self.service.name} ({self.status})"
#         return f"{self.client.user.email} - Custom Service ({self.status})"


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


class BookingRequest(models.Model):

    class BookingType(models.TextChoices):
        ONE_TIME = "one_time", "One-Time"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Biweekly"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"     # landscaper accepted
        CONFIRMED = "confirmed", "Confirmed"  # client confirmed price (request/custom)
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