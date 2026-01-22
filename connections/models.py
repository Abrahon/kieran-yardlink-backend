from django.db import models

# Create your models here.
from django.db import models
from accounts.models import User

class ConnectionRequest(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_requests"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_requests"
    )

    is_accepted = models.BooleanField(null=True)  
    # None = pending | True = accepted | False = rejected

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender} → {self.receiver}"
