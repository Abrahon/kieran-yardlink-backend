




from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from property.models import Property
from profiles.models import ExternalClient   # <-- adjust app path if needed

from bookings.models import BookingRequest
from landscapers.models import Service, Addon, BusinessProfile
from profiles.models import ClientProfile
from property.models import Property



class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Job(TimeStampedModel):
    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        RESCHEDULED = "rescheduled", "Rescheduled"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"

    booking = models.OneToOneField(
        BookingRequest,
        on_delete=models.CASCADE,
        related_name="job",
        null=True,
        blank=True,
    )

    # REGULAR APP CLIENT
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )

    # NEW: EXTERNAL CLIENT
    external_client = models.ForeignKey(
        ExternalClient,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )

    landscaper = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    job_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True
    )

    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        # Must have exactly one client type
        if self.client and self.external_client:
            raise ValidationError("A job cannot have both a regular client and an external client.")

        if not self.client and not self.external_client:
            raise ValidationError("A job must have either a regular client or an external client.")

        # Booking only works with regular app client
        if self.booking:
            if not self.client:
                raise ValidationError("A booking-based job must have a regular app client.")
            if self.external_client:
                raise ValidationError("A booking-based job cannot use an external client.")
            if self.booking.client != self.client:
                raise ValidationError("Job client must match booking client.")
            if self.booking.landscaper != self.landscaper:
                raise ValidationError("Job landscaper must match booking landscaper.")

        # External client must belong to same landscaper
        if self.external_client and self.external_client.landscaper != self.landscaper:
            raise ValidationError("External client must belong to this landscaper.")

    @property
    def total_items(self):
        return self.items.count()

    @property
    def completed_items(self):
        return self.items.filter(is_completed=True).count()

    @property
    def client_name(self):
        if self.client:
            return self.client.user.get_full_name() or self.client.user.email
        if self.external_client:
            return self.external_client.name
        return None

    @property
    def client_email(self):
        if self.client:
            return self.client.user.email
        if self.external_client:
            return self.external_client.email
        return None

    @property
    def client_phone(self):
        if self.client:
            return getattr(self.client, "phone", None)
        if self.external_client:
            return self.external_client.phone
        return None

    def recalculate_total_price(self, save=True):
        total = self.items.filter(is_completed=True).aggregate(
            total=models.Sum("price")
        )["total"] or Decimal("0.00")

        self.total_price = total

        if save:
            self.save(update_fields=["total_price", "updated_at"])

        return self.total_price

    def has_before_images(self):
        return self.images.filter(image_type=JobImage.ImageType.BEFORE).exists()

    def has_after_images(self):
        return self.images.filter(image_type=JobImage.ImageType.AFTER).exists()

    def update_status_from_items(self, save=True):
        total_items = self.items.count()
        completed_items = self.items.filter(is_completed=True).count()

        if total_items == 0:
            new_status = self.Status.UPCOMING
        elif completed_items == 0:
            new_status = self.Status.UPCOMING
        elif completed_items < total_items:
            new_status = self.Status.IN_PROGRESS
        else:
            new_status = self.Status.COMPLETED

        self.status = new_status
        self.completed_at = timezone.now() if new_status == self.Status.COMPLETED else None

        if save:
            self.save(update_fields=["status", "completed_at", "updated_at"])

        return new_status

    def can_be_completed(self):
        total_items = self.items.count()
        completed_items = self.items.filter(is_completed=True).count()

        if total_items == 0:
            raise ValidationError("This job has no items.")
        if completed_items != total_items:
            raise ValidationError("All job items must be completed first.")

    def mark_completed(self):
        self.can_be_completed()
        self.recalculate_total_price(save=False)
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()

        if not self.payment_status:
            self.payment_status = self.PaymentStatus.PENDING

        self.save(update_fields=["total_price", "status", "completed_at", "payment_status", "updated_at"])

    def __str__(self):
        return f"Job #{self.id} - {self.client_name or 'No Client'} - {self.status}"



class JobItem(TimeStampedModel):
    class ItemType(models.TextChoices):
        STANDARD_SERVICE = "standard_service", "Standard Service"
        ADDON = "addon", "Addon"
        CUSTOM = "custom", "Custom"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="job_items")
    addon = models.ForeignKey(Addon, on_delete=models.SET_NULL, null=True, blank=True, related_name="job_items")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)])
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="completed_job_items")
    note = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def clean(self):
        if self.item_type == self.ItemType.STANDARD_SERVICE and not self.service:
            raise ValidationError("Standard service item must have a service.")
        if self.item_type == self.ItemType.ADDON and not self.addon:
            raise ValidationError("Addon item must have an addon.")
        if self.item_type == self.ItemType.CUSTOM and not self.name:
            raise ValidationError("Custom item must have a name.")

    def mark_complete(self, user=None):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=["is_completed", "completed_at", "completed_by", "updated_at"])
        self.job.recalculate_total_price()
        self.job.update_status_from_items()

    def mark_incomplete(self):
        self.is_completed = False
        self.completed_at = None
        self.completed_by = None
        self.save(update_fields=["is_completed", "completed_at", "completed_by", "updated_at"])
        self.job.recalculate_total_price()
        self.job.update_status_from_items()

    def __str__(self):
        return f"Job #{self.job.id} - {self.name}"



from cloudinary.models import CloudinaryField

class JobImage(TimeStampedModel):
    class ImageType(models.TextChoices):
        BEFORE = "before", "Before"
        AFTER = "after", "After"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField('image')  # CloudinaryField here
    image_type = models.CharField(max_length=10, choices=ImageType.choices)
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_images"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Job #{self.job.id} - {self.image_type}"


class JobReschedule(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="reschedules")
    old_date = models.DateField()
    old_time = models.TimeField()
    new_date = models.DateField()
    new_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="job_reschedule_requests")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job #{self.job.id} rescheduled"

   