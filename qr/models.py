import uuid
from django.db import models
from landscapers.models import BusinessProfile  # no space after dot

class LandscaperQRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    landscaper = models.OneToOneField(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="qr_code"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR for {self.landscaper.user.email} ({self.id})"


# class LandscaperQRCode(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     landscaper = models.OneToOneField(
#         BusinessProfile,
#         on_delete=models.CASCADE,
#         related_name="qr_code"
#     )

#     token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

#     created_at = models.DateTimeField(auto_now_add=True)