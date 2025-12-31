from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .enums import SubscriptionDuration, SubscriptionStatus

User = get_user_model()

class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    duration = models.CharField(max_length=20, choices=SubscriptionDuration.choices,
                                default=SubscriptionDuration.MONTHLY)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def duration_days(self):
        mapping = {
            SubscriptionDuration.MONTHLY: 30,
            SubscriptionDuration.YEARLY: 365,
        }
        return mapping.get(self.duration, 30)

    def __str__(self):
        return f"{self.name} ({self.duration})"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices,
                              default=SubscriptionStatus.ACTIVE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def extend(self):
        days = 30 if self.plan.duration == "monthly" else 365
        self.end_date += timedelta(days=days)
        self.save()

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
