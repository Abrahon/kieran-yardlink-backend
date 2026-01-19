from django.urls import path
from .views import create_checkout_session, CashPaymentAPIView, stripe_webhook

urlpatterns = [
    path("bookings/<int:booking_id>/pay-online/", create_checkout_session),
    path("bookings/<int:booking_id>/pay-cash/", CashPaymentAPIView.as_view()),
    path("stripe/webhook/", stripe_webhook),
]
