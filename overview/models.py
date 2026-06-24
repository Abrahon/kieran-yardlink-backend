from django.db import models

# Create your models here.

# activity/models.py

from django.db import models
from django.conf import settings


class ActivityLog(models.Model):

    class Action(models.TextChoices):
        USER_SIGNUP = "user_signup", "User Signup"
        INVOICE_SENT = "invoice_sent", "Invoice Sent"
        PAYMENT_COMPLETED = "payment_completed", "Payment Completed"
        PLAN_UPGRADED = "plan_upgraded", "Plan Upgraded"
        ACCOUNT_SUSPENDED = "account_suspended", "Account Suspended"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50,
        choices=Action.choices
    )

    description = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action}"
