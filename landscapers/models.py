
from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# Landscaper Profile (basic info + business info)
class LandscaperProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaper_profile"
    )

    profile_image = CloudinaryField(
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


# Service model
class Service(models.Model):
    class CategoryChoices(models.TextChoices):
        STANDARD = "standard", _("Standard")
        CUSTOM = "custom", _("Custom")

    class StandardServiceChoices(models.TextChoices):
        LAWN_MOWING = "lawn_mowing", _("Lawn Mowing")
        GARDEN_DESIGN = "garden_design", _("Garden Design")
        TREE_TRIMMING = "tree_trimming", _("Tree Trimming")
        FERTILIZATION = "fertilization", _("Fertilization")
        IRRIGATION = "irrigation", _("Irrigation")

    landscaper = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="services"
    )

    standard_services = models.JSONField(default=list, blank=True)
    custom_service = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.STANDARD
    )
    add_ons = models.JSONField(default=list, blank=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=14)
    longitude = models.DecimalField(max_digits=20, decimal_places=14)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_square_feet = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.custom_service if self.custom_service else ", ".join(self.standard_services)


# Working Hours model
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
        LandscaperProfile,
        on_delete=models.CASCADE,
        related_name='working_hours'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)

    class Meta:
        unique_together = ('landscaper', 'day')

    def __str__(self):
        return f"{self.landscaper.business_name} - {self.day}"
