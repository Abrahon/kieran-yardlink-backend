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
      
    schedule = models.OneToOneField(
        "jobs.Job",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connection"
    )

    is_accepted = models.BooleanField(null=True)
      
    # None = pending | True = accepted | False = rejected
    already_sent = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender} → {self.receiver}"
