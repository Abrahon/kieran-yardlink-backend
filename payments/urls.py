from django.urls import path
from .views import (
    create_schedule_checkout_session,
    CashPaymentScheduleAPIView,
    stripe_webhook,
    payment_success,
    payment_cancel,
    landscaper_payment_history
)

urlpatterns = [
    path("schedule/pay-online/", create_schedule_checkout_session),
    path("schedule/<int:schedule_id>/pay-cash/", CashPaymentScheduleAPIView.as_view()),
    path("stripe/webhook/", stripe_webhook),
    path("payments/history/", landscaper_payment_history),

    # Stripe redirect URLs
    path("success/", payment_success),
    path("cancel/", payment_cancel),
]
