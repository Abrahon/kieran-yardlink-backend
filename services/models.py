from django.db import models
from landscapers.models import LandscaperProfile
from .enums import ServiceCategory

class Service(models.Model):
    landscaper = models.ForeignKey(
        LandscaperProfile,
        on_delete=models.CASCADE,
        related_name="services"
    )

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=ServiceCategory.choices
    )

    is_addon = models.BooleanField(default=False)

    # New fields
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Only Pro landscapers can set this"
    )
    square_feet = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Only Pro landscapers can set this"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("landscaper", "name")

    def __str__(self):
        return f"{self.name} ({self.landscaper.user.email})"
