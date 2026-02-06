
from django.db import models

class PaymentStatus(models.TextChoices):
    PENDING = "pending"
    PAID = "paid"
    CASH_PENDING = "cash_pending"
