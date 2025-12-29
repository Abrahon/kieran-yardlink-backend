from django.db import models
from accounts.models import User
from .enums import GrassTypeChoices
from cloudinary.models import CloudinaryField

class Property(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="properties"
    )

    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    PROPERTY_SIZE_CHOICES = [
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
    ]
    property_size = models.CharField(
        max_length=10, choices=PROPERTY_SIZE_CHOICES
    )

    cut_height_inches = models.DecimalField(
        max_digits=4, decimal_places=2
    )

    grass_types = models.JSONField(
        default=list,
        help_text="Example: ['bermuda']"
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate grass types against enum"""
        valid_values = GrassTypeChoices.values
        for grass in self.grass_types:
            if grass not in valid_values:
                raise ValueError(f"Invalid grass type: {grass}")

    def __str__(self):
        return f"{self.address}"








class PropertyPhoto(models.Model):
    property = models.ForeignKey(
        "Property",
        on_delete=models.CASCADE,
        related_name="photos"
    )
    image = CloudinaryField(
        "property_photo",
        folder="property_photos"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
