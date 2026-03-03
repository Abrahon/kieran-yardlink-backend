
from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _
# from profiles.models import LandscaperProfilies
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField, JSONField  # PostgreSQL
User = get_user_model()
from django.core.exceptions import ValidationError


# Landscaper Profile (business info)
class BusinessProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business_profile"
    )

    # Business info
    business_name = models.CharField(max_length=150)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)

    # Optional tagline / slogan
    tagline = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text="Short description or tagline about the business"
    )

    # Optional business description
    description = models.TextField(
        max_length=500,
        blank=True,
        null=True
    )

    # Location
    latitude = models.DecimalField(
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True
    )

    # Profile image (Pro only — validated via subscription app)
    profile_image = CloudinaryField(
        "pro_landscaper",
        blank=True,
        null=True
    )

    # QuickBooks integration (Pro only — validated via subscription app)
    quickbooks_connected = models.BooleanField(default=False)

    # Either Insurance or License document
    insurance_doc = CloudinaryField(
        "insurance_doc",
        blank=True,
        null=True,
        help_text="Upload business insurance document if required"
    )
    license_doc = CloudinaryField(
        "license_doc",
        blank=True,
        null=True,
        help_text="Upload business license document if required"
    )

    # Profile complete flag
    is_profile_completed = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validation: only one of insurance_doc or license_doc can be uploaded
        if self.insurance_doc and self.license_doc:
            raise ValidationError("You can upload either insurance OR license document, not both.")

    def __str__(self):
        return self.business_name


class Service(models.Model):

    class PricingType(models.TextChoices):
        FIXED = "fixed", "Fixed Price"
        REQUEST = "request", "Priced Upon Request"

    # FK to BusinessProfile
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="services",
        null=False,   # non-nullable
        blank=False
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    pricing_type = models.CharField(
        max_length=10,
        choices=PricingType.choices,
        default=PricingType.FIXED
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )

    # Location (optional)
    latitude = models.DecimalField(
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=20,
        decimal_places=18,
        null=True,
        blank=True
    )

    # Status & pinning
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "is_active"]),
            models.Index(fields=["pricing_type"]),
            models.Index(fields=["is_pinned"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_service_per_business"
            )
        ]

    def clean(self):
        # Fixed → base_price required
        if self.pricing_type == self.PricingType.FIXED and self.base_price is None:
            raise ValidationError("Fixed pricing requires base_price.")
        # Request → base_price must be empty
        if self.pricing_type == self.PricingType.REQUEST and self.base_price is not None:
            raise ValidationError("Request pricing should not have base_price.")

    def __str__(self):
        return f"{self.name} ({self.business.business_name})"




class ClientCustomService(models.Model):
    client = models.ForeignKey(
        "profiles.ClientProfile",
        on_delete=models.CASCADE,
        related_name="custom_services"
    )

    name = models.CharField(
        max_length=150,
        help_text="Custom service name"
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Service description"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Service price"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate instead of delete"
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "name"],
                name="unique_custom_service_per_client"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.client.user.email})"


class Addon(models.Model):
    business = models.ForeignKey(
        "profiles.LandscaperProfilies",  # string reference
        on_delete=models.CASCADE,
        related_name="addons"
    )

    name = models.CharField(
        max_length=150,
        help_text="Add-On নাম"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="অতিরিক্ত মূল্য"
    )


    applicable_service_ids = models.JSONField(
        blank=True,
        default=list,
        help_text="Applicable service IDs"
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["business"]),
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_addon_per_business"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.business.business_name})"




# working_hours/models.py
DAYS_OF_WEEK = [
    ('SUNDAY', 'Sunday'),
    ('MONDAY', 'Monday'),
    ('TUESDAY', 'Tuesday'),
    ('WEDNESDAY', 'Wednesday'),
    ('THURSDAY', 'Thursday'),
    ('FRIDAY', 'Friday'),
    ('SATURDAY', 'Saturday'),
]

class WorkingHours(models.Model):
    landscaper = models.ForeignKey(
        "landscapers.BusinessProfile", 
        on_delete=models.CASCADE,
        related_name="working_hours"
    )

    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('landscaper', 'day')

    def __str__(self):
        return f"{self.landscaper.name} - {self.day}"
