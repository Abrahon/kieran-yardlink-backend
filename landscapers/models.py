from django.db import models
from accounts.models import User
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model

User = get_user_model()

class LandscaperProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaper_profile"
    )

    profile = CloudinaryField(
        "pro_landscaper",
        blank=True,
        null=True
    )

    business_name = models.CharField(max_length=150)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)

    latitude = models.DecimalField(max_digits=20, decimal_places=14)
    longitude = models.DecimalField(max_digits=20, decimal_places=14)

    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

# service model
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Service(models.Model):
    class StandardServiceChoices(models.TextChoices):
        LAWN_MOWING = "lawn_mowing", _("Lawn Mowing")
        GARDEN_DESIGN = "garden_design", _("Garden Design")
        TREE_TRIMMING = "tree_trimming", _("Tree Trimming")
        FERTILIZATION = "fertilization", _("Fertilization")
        IRRIGATION = "irrigation", _("Irrigation")
        # Add more as needed

    class CategoryChoices(models.TextChoices):
        STANDARD = "standard", _("Standard")
        CUSTOM = "custom", _("Custom")

    landscaper = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="services"
    )

    # Multi-select standard services (array of choice strings)
    standard_services = models.JSONField(default=list, blank=True)
    # Example: ["lawn_mowing", "tree_trimming"]

    # Custom service if not in predefined
    custom_service = models.CharField(max_length=150, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.STANDARD
    )

    # Optional add-ons (array of dicts)
    add_ons = models.JSONField(default=list, blank=True)
    # Example: [{"name": "Extra Fertilizer", "price": 500}]

    # Location for service (map coordinates)
    latitude = models.DecimalField(max_digits=20, decimal_places=14)
    longitude = models.DecimalField(max_digits=20, decimal_places=14)

    # Price details
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_square_feet = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price per square foot"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.custom_service:
            return f"{self.custom_service} ({self.landscaper.email})"
        return f"{', '.join(self.standard_services)} ({self.landscaper.email})"



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
    landscaper = models.ForeignKey(LandscaperProfile, on_delete=models.CASCADE, related_name='working_hours')
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)

    class Meta:
        unique_together = ('landscaper', 'day')  # Each day only once
