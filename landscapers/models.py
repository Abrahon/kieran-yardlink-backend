from django.db import models
from accounts.models import User
from cloudinary.models import CloudinaryField


# class LandscaperProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="landscaper_profile"
#     )
#     # user = models.OneToOneField(User, on_delete=models.CASCADE)
#     profile = CloudinaryField("pro_landscaper", blank=True, null=True)  # fixed name typo

#     business_name = models.CharField(max_length=150)
#     business_email = models.EmailField()
#     business_phone = models.CharField(max_length=20)

#     service_address = models.CharField(max_length=255)
#     latitude = models.DecimalField(max_digits=20, decimal_places=14)
#     longitude = models.DecimalField(max_digits=20, decimal_places=14)

#     is_profile_completed = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.business_name

from django.db import models
from cloudinary.models import CloudinaryField

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

    service_address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=20, decimal_places=14)
    longitude = models.DecimalField(max_digits=20, decimal_places=14)

    # ✅ Standard services (multiple selection)
    standard_services = models.JSONField(
        default=list,
        blank=True,
        help_text="List of standard services selected by landscaper"
    )

    # ✅ Optional add-ons (multiple selection)
    add_ons = models.JSONField(
        default=list,
        blank=True,
        help_text="Optional add-on services"
    )

    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


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
