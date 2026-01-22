from django.db import models
from accounts.models import User
from .enums import GrassTypeChoices

class Property(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="properties"
    )

    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    # Removed choices; now just a text field
    property_size = models.TextField(
        help_text="Size of the property (e.g., '1 ac', '120 m²', '5000 ft²')"
    )

    cut_height_inches = models.DecimalField(max_digits=4, decimal_places=2)

    grass_types = models.JSONField(default=list)

    notes = models.TextField(blank=True)

    # ✅ Images stored here
    images = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.address} ({self.property_size})"

