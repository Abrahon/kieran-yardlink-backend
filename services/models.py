
from django.db import models
from landscapers.models import BusinessProfile
from profiles.models import ClientProfile,LandscaperProfilies
from cloudinary.models import CloudinaryField
from landscapers .models import Service
from profiles .models import LandscaperProfilies


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



# TODO 
# services/models.py
from django.conf import settings

class AddOnService(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="add_on_services"
    )
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'name')  # Same client can't create duplicate names

    def __str__(self):
        return f"{self.name} - ${self.price}"





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
    completion_note = models.TextField(null=True, blank=True)

    # # NEW FIELDS FOR MULTI-SERVICE COMPLETION
    completed_services = models.ManyToManyField(
        ClientService,
        blank=True,
        related_name="completed_jobs"
    )

    #  PAYMENT FIELDS (THIS IS WHAT YOU WERE MISSING)
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

# TODO Job instead of service schedule

# from django.db import models
# from django.core.validators import MinValueValidator

# class Job(models.Model):
#     class JobStatus(models.TextChoices):
#         SCHEDULED = "scheduled", "Scheduled"
#         COMPLETED = "completed", "Completed"
#         CANCELLED = "cancelled", "Cancelled"

#     class PaymentStatus(models.TextChoices):
#         PENDING = "pending", "Pending"
#         PAID = "paid", "Paid"
#         FAILED = "failed", "Failed"

#     client = models.ForeignKey(
#         "yourapp.ClientProfile",
#         on_delete=models.CASCADE,
#         related_name="jobs"
#     )

#     landscaper = models.ForeignKey(
#         "yourapp.LandscaperProfile",
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="jobs"
#     )

#     # Support both standard + custom service
#     service = models.ForeignKey(
#         "yourapp.Service",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="jobs"
#     )

#     custom_service = models.ForeignKey(
#         "yourapp.ClientCustomService",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="jobs"
#     )

#     # Multi-service completion (optional)
#     completed_services = models.ManyToManyField(
#         "yourapp.ClientService",
#         blank=True,
#         related_name="completed_jobs"
#     )

#     scheduled_date = models.DateField()
#     scheduled_time = models.TimeField(null=True, blank=True)

#     status = models.CharField(
#         max_length=10,
#         choices=JobStatus.choices,
#         default=JobStatus.SCHEDULED
#     )

#     completion_note = models.TextField(null=True, blank=True)
#     completed_at = models.DateTimeField(null=True, blank=True)

#     total_price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(0)],
#         null=True,
#         blank=True
#     )

#     payment_status = models.CharField(
#         max_length=10,
#         choices=PaymentStatus.choices,
#         default=PaymentStatus.PENDING
#     )
#     stripe_payment_id = models.CharField(max_length=255, null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["scheduled_date", "scheduled_time"]
#         indexes = [
#             models.Index(fields=["client", "status"]),
#             models.Index(fields=["scheduled_date"]),
#             models.Index(fields=["landscaper"]),
#         ]

#     def clean(self):
#         from django.core.exceptions import ValidationError

#         if not self.service and not self.custom_service:
#             raise ValidationError("Either standard service or custom service must be set.")

#     def __str__(self):
#         service_name = self.service.name if self.service else self.custom_service.name
#         return f"Job {service_name} @ {self.scheduled_date} {self.scheduled_time}"


# ---------------- Proof Images (Per Job) ----------------
class ScheduleCompletionImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ("before", "Before"),
        ("after", "After")
    ]
    schedule = models.ForeignKey(
        ServiceSchedule,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = CloudinaryField("completed-work")
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, default="after")
    uploaded_at = models.DateTimeField(auto_now_add=True)


# TODO ADDON job

# from django.db import models
# from django.core.validators import MinValueValidator

# class JobAddon(models.Model):
#     job = models.ForeignKey(
#         "yourapp.Job",  # আপনার Job model নাম অনুযায়ী
#         on_delete=models.CASCADE,
#         related_name="addons"
#     )

#     addon = models.ForeignKey(
#         "yourapp.Addon",  # আপনার Addon model নাম অনুযায়ী
#         on_delete=models.CASCADE,
#         related_name="job_addons"
#     )

#     price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(0)]
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["-created_at"]
#         indexes = [
#             models.Index(fields=["job"]),
#             models.Index(fields=["addon"]),
#         ]
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["job", "addon"],
#                 name="unique_addon_per_job"
#             )
#         ]

#     def __str__(self):
#         return f"{self.addon.name} for Job {self.job.id} - ${self.price}"