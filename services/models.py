
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






