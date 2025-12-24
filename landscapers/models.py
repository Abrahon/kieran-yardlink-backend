from django.db import models
from accounts.models import User
from cloudinary.models import CloudinaryField

class LandscaperProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaper_profile"
    )
    profile = CloudinaryField("pro_landscaper", blank=True, null=True)  # fixed name typo

    business_name = models.CharField(max_length=150)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)

    service_address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=20, decimal_places=14)
    longitude = models.DecimalField(max_digits=20, decimal_places=14)

    is_profile_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name
