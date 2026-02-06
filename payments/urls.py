from django.urls import path
from .views import (
    create_schedule_checkout_session,
    CashPaymentScheduleAPIView,
    stripe_webhook,
    payment_success,
    payment_cancel,
    landscaper_payment_history,
    admin_transaction_summary,
    admin_daily_income_overview,
    stripe_all_payments,
    delete_single_payment,
    ProLandscaperMonthlyRevenueView
)

urlpatterns = [
    # =========================
    # Client Payments
    # =========================
    path("schedule/pay-online/", create_schedule_checkout_session),
    path("schedule/<int:schedule_id>/pay-cash/", CashPaymentScheduleAPIView.as_view()),

    # =========================
    # Stripe
    # =========================
    path("stripe/webhook/", stripe_webhook),
    path("success/", payment_success),
    path("cancel/", payment_cancel),
    # Landscaper
    path("payments/history/", landscaper_payment_history),
    # Admin
    path(
        "admin/transactions/summary/",
        admin_transaction_summary,
        name="admin-transaction-summary"
    ),
    path(
        "admin/stripe/daily-overview/",
        admin_daily_income_overview,
        name="admin-stripe-daily-overview"
    ),
    path(
        "admin/stripe/payments/",
        stripe_all_payments,
        name="admin-stripe-all-payments"
    ),
    path(
        "admin/stripe/payments/<str:source>/<int:pk>/delete/",
         delete_single_payment,
        name="admin-stripe-all-payments-delete"
    ),

    path(
        "landscaper/pro/monthly-revenue/",
        ProLandscaperMonthlyRevenueView.as_view(),
        name="pro-landscaper-monthly-revenue"
    ),

]
