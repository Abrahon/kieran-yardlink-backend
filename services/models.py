# from django.db import models
# from landscapers.models import LandscaperProfile
# from profiles.models import ClientProfile
# from .enums import ServiceCategory

# class Service(models.Model):
#     landscaper = models.ForeignKey(
#         LandscaperProfile,
#         on_delete=models.CASCADE,
#         related_name="services"
#     )

#     name = models.CharField(max_length=120)
#     description = models.TextField(blank=True)
#     category = models.CharField(
#         max_length=50,
#         choices=ServiceCategory.choices
#     )


#     # New fields
#     price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         null=True,
#         blank=True,
#         help_text="Only Pro landscapers can set this"
#     )
#     square_feet = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         null=True,
#         blank=True,
#         help_text="Only Pro landscapers can set this"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["-created_at"]
#         unique_together = ("landscaper", "name")

#     def __str__(self):
#         return f"{self.name} ({self.landscaper.user.email})"



# # CLIENT MODEL
# # CLIENT MODEL
# class ClientServicePreference(models.Model):
#     client = models.ForeignKey(
#         ClientProfile,
#         on_delete=models.CASCADE,
#         related_name="service_preferences"
#     )

#     services = models.ManyToManyField(
#         Service,
#         related_name="selected_by_clients",
#         blank=True
#     )

#     frequency = models.CharField(
#         max_length=20,
#         choices=[
#             ("weekly", "Weekly"),
#             ("biweekly", "Bi-Weekly"),
#             ("monthly", "Monthly"),
#         ]
#     )

#     note = models.TextField(blank=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Preferences of {self.client.user.email}"

from django.db import models
from landscapers.models import LandscaperProfile
from profiles.models import ClientProfile

class Service(models.Model):
    landscaper = models.ForeignKey(
        LandscaperProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="services"
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    square_feet = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_standard = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("landscaper", "name")

    def __str__(self):
        return self.name



# from profiles.models import ClientProfile

class ClientServicePreference(models.Model):
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="service_preferences"
    )
    services = models.ManyToManyField(
        Service,
        related_name="selected_by_clients",
        blank=True
    )
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

    def __str__(self):
        return f"Preferences of {self.client.user.email}"
