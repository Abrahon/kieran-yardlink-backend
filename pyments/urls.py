from django.urls import path
from .views import (
    create_schedule_checkout_session,
    CashPaymentScheduleAPIView,
    stripe_webhook
)

urlpatterns = [
    path("schedule/<int:schedule_id>/pay-online/", create_schedule_checkout_session),
    path("schedule/<int:schedule_id>/pay-cash/", CashPaymentScheduleAPIView.as_view()),
    path("stripe/webhook/", stripe_webhook),
]
