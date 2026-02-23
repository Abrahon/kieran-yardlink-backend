# from django.db import models
# from services .models import ServiceSchedule
# from .enums import PaymentStatus
# from django.db import models

# class PaymentStatus(models.TextChoices):
#     PENDING = "pending"
#     PAID = "paid"
#     CASH_PENDING = "cash_pending"



# # Create your models here.
# class Payment(models.Model):
#     job = models.OneToOneField(
#         ServiceSchedule,
#         on_delete=models.CASCADE,
#         related_name="payment"
#     )

#     stripe_payment_id = models.CharField(max_length=255)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_status = models.CharField(
#         max_length=20,
#         choices=PaymentStatus.choices
#     )

#     created_at = models.DateTimeField(auto_now_add=True)