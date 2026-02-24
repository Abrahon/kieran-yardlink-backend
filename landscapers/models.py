
from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _
# from profiles.models import LandscaperProfilies

User = get_user_model()

# Landscaper Profile (business info)
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

    latitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)

    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


# updated  models
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

# add new models  fo add ons


# Service model
# class Service(models.Model):
#     class CategoryChoices(models.TextChoices):
#         STANDARD = "standard", _("Standard")
#         CUSTOM = "custom", _("Custom")

#     class StandardServiceChoices(models.TextChoices):
#         LAWN_MOWING = "lawn_mowing", _("Lawn Mowing")
#         GARDEN_DESIGN = "garden_design", _("Garden Design")
#         TREE_TRIMMING = "tree_trimming", _("Tree Trimming")
#         FERTILIZATION = "fertilization", _("Fertilization")
#         IRRIGATION = "irrigation", _("Irrigation")

#     landscaper = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="services"
#     )
#     # landscaper = models.ForeignKey(LandscaperProfilies, on_delete=models.CASCADE)
    

#     standard_services = models.JSONField(default=list, blank=True)
#     custom_service = models.CharField(max_length=150, blank=True, null=True)
#     description = models.TextField(blank=True, null=True)
#     category = models.CharField(
#         max_length=20,
#         choices=CategoryChoices.choices,
#         default=CategoryChoices.STANDARD
#     )
#     add_ons = models.JSONField(default=list, blank=True)
#     latitude = models.DecimalField(max_digits=20, decimal_places=18)
#     latitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
#     longitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     per_square_feet = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.custom_service if self.custom_service else ", ".join(self.standard_services)


from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class Service(models.Model):
    class CategoryChoices(models.TextChoices):
        STANDARD = "standard", _("Standard")
        CUSTOM = "custom", _("Custom")

    class RateTypeChoices(models.TextChoices):
        FLAT = "flat", _("Flat Rate")
        HOURLY = "hourly", _("Hourly")

    landscaper = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="services"
    )
    standard_service = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=20, choices=CategoryChoices.choices, default=CategoryChoices.STANDARD
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    time = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Duration in hours"
    )
    rate_type = models.CharField(max_length=10, choices=RateTypeChoices.choices)
    latitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.standard_service or "Custom Service"



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
        LandscaperProfile,  
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

# serializers for standard services 
# from rest_framework import serializers
# from .models import StandardService, ClientServicePreference

# class StandardServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StandardService
#         fields = ["id", "name", "pricing_type", "base_price", "is_active"]
#         read_only_fields = ["id"]

# class StandardServiceUpdateByLandscaperSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StandardService
#         fields = ["pricing_type", "base_price", "is_active"]

# class ClientServicePreferenceSerializer(serializers.ModelSerializer):
#     services = StandardServiceSerializer(many=True, read_only=True)
#     service_ids = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=StandardService.objects.filter(is_active=True),
#         write_only=True,
#         source="services"
#     )
#     total_price = serializers.SerializerMethodField()

#     class Meta:
#         model = ClientServicePreference
#         fields = ["client", "services", "service_ids", "frequency", "note", "total_price", "updated_at"]
#         read_only_fields = ["client", "total_price", "updated_at"]

#     def get_total_price(self, obj):
#         total = 0
#         for service in obj.services.all():
#             qty = 1 if service.pricing_type in ["hourly","flat"] else 100
#             total += float(service.base_price) * qty
#         return total

#     def update(self, instance, validated_data):
#         services = validated_data.pop('services', [])
#         if services:
#             instance.services.set(services)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance

#     def create(self, validated_data):
#         client = self.context['request'].user.clientprofile
#         services = validated_data.pop('services', [])
#         obj, created = ClientServicePreference.objects.update_or_create(
#             client=client,
#             defaults=validated_data
#         )
#         obj.services.set(services)
#         return obj
