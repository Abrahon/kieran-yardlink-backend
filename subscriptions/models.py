from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .enums import SubscriptionDuration, SubscriptionStatus
from decimal import Decimal 

User = get_user_model()

# plan model
class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    duration = models.CharField(max_length=20, choices=SubscriptionDuration.choices,default=SubscriptionDuration.MONTHLY)                        
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
    
    
    @property
    def final_price(self):
        price = Decimal(self.price)
        discount = Decimal(self.discount)

        # assuming discount is percentage
        return price - (price * discount / Decimal("100"))

    def __str__(self):
        return f"{self.name} ({self.duration})"


# subscription model
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    # NEW FIELD: Track free trial
    is_trial = models.BooleanField(default=False)  

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # 🔹 New field to track auto-renew toggle
    auto_renew = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    # 🔹 Only paid subscriptions can auto-renew
    def check_auto_renew(self):
        now = timezone.now()
        if self.is_trial:
            # Trial subscriptions never auto-renew
            return False

        if self.auto_renew and self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED] and self.end_date <= now:
            # Extend subscription by plan duration
            duration_days = self.plan.duration_days
            self.start_date = now
            self.end_date = now + timedelta(days=duration_days)
            self.status = SubscriptionStatus.ACTIVE
            self.save(update_fields=["start_date", "end_date", "status"])
            return True
        return False