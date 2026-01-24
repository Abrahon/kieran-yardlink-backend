from django.db import models
from accounts.models import User
from cloudinary.models import CloudinaryField
from property.models import Property
from django.db.models import JSONField  # for Django 4+

class Job(models.Model):
    landscaper = models.ForeignKey(User, on_delete=models.CASCADE, related_name="landscaper_jobs")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_jobs")
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("completed", "Completed")
        ],
        default="pending"
    )
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_reduced = models.BooleanField(default=False)
    
    # Store multiple image URLs here as a JSON array
    images = JSONField(default=list, blank=True)

    # New notes field
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

