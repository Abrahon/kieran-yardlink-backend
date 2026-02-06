from django.db import models

# Create your models here.

from accounts.models import User

class NotificationSettings(models.Model):
    """
    Notification preferences for Pro landscapers.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_settings")
    job_alert = models.BooleanField(default=True)
    payment_alert = models.BooleanField(default=True)
    weather_alert = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification settings for {self.user.username}"


class Notification(models.Model):
    """
    Stores individual notifications.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ("job", "Job"),
        ("payment", "Payment"),
        ("weather", "Weather"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"
