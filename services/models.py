
from django.db import models
from landscapers.models import LandscaperProfile
from profiles.models import ClientProfile,LandscaperProfilies
from cloudinary.models import CloudinaryField


# admin add standard service
# class StandardService(models.Model):
#     class PricingType(models.TextChoices):
#         HOURLY = "hourly", _("Hourly")
#         FLAT = "flat", _("Flat Rate")
#         PER_SQFT = "per_sqft", _("Per Square Foot")

#     name = models.CharField(max_length=120, unique=True)
#     pricing_type = models.CharField(
#         max_length=20,
#         choices=PricingType.choices,
#         default=PricingType.HOURLY
#     )
#     base_price = models.DecimalField(max_digits=10, decimal_places=2)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name




# ---------------- Client Service (Client-facing services) ----------------
class ClientService(models.Model):
    landscaper = models.ForeignKey(
        LandscaperProfilies,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    square_feet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_standard = models.BooleanField(default=False)
    image = CloudinaryField("service-image", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("landscaper", "name")

    def __str__(self):
        return self.name



# ---------------- Client Service Preference ----------------
class ClientServicePreference(models.Model):
    client = models.OneToOneField(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="service_preference"
    )
    services = models.ManyToManyField(ClientService, blank=True)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ("weekly", "Weekly"),
            ("biweekly", "Bi-Weekly"),
            ("monthly", "Monthly"),
        ]
    )
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------------- Client Job / Schedule ----------------

class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    CASH_PENDING = "cash_pending", "Cash Pending"


class ServiceSchedule(models.Model):
    service = models.ForeignKey(
        ClientService,
        on_delete=models.CASCADE,
        related_name="schedules"
    )
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE)
    landscaper = models.ForeignKey(
        LandscaperProfilies,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="jobs"
    )

    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)

    # Job status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # 💰 PAYMENT FIELDS (THIS IS WHAT YOU WERE MISSING)
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    stripe_payment_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_date", "scheduled_time"]

    def __str__(self):
        return f"{self.service.name} @ {self.scheduled_date} {self.scheduled_time}"


# ---------------- Proof Images (Per Job) ----------------
class ScheduleCompletionImage(models.Model):
    schedule = models.ForeignKey(
        ServiceSchedule,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = CloudinaryField("completed-work")

    uploaded_at = models.DateTimeField(auto_now_add=True)