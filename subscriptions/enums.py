from django.db import models

class SubscriptionDuration(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    TRIALING = "trialing", "Trialing"
    CANCELLED = "cancelled", "Cancelled"
