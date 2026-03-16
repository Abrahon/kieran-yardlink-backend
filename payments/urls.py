from django.urls import path
from .views import (
    create_invoice_checkout_session,
    CashPaymentScheduleAPIView,
    stripe_webhook,
    payment_success,
    payment_cancel,
    landscaper_payment_history,
    admin_transaction_summary,
    admin_daily_income_overview,
    stripe_all_payments,
    ProLandscaperMonthlyRevenueView,
    RecentPaymentsAPIView,
    client_payment_history,
    delete_user_financial_data,
    ConfirmCashPaymentAPIView,
    admin_income_overview,
    AdminStripeVsCashDashboardAPIView

    
)


urlpatterns = [

    # Client Payments

    path("schedule/pay-online/", create_invoice_checkout_session),
       # -------------------------------
    # Client selects cash payment for a completed service
    # POST: /client/services/<schedule_id>/cash-payment/
    # -------------------------------
    path(
        "client/services/<int:schedule_id>/cash-payment/",
        CashPaymentScheduleAPIView.as_view(),
        name="client-cash-payment"
    ),

    # -------------------------------
    # Landscaper confirms cash payment received
    # POST: /landscaper/services/<schedule_id>/confirm-cash-payment/
    # -------------------------------
    path(
        "landscaper/services/<int:schedule_id>/confirm-cash-payment/",
        ConfirmCashPaymentAPIView.as_view(),
        name="landscaper-confirm-cash-payment"
    ),

    # Stripe
    path("payment/webhook/", stripe_webhook),
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
        "admin/stripe/monthly-overview/",
        admin_income_overview,
        name="admin-stripe-monthly-overview"
    ),
    path(
        "admin/stripe/payments/",
        stripe_all_payments,
        name="admin-stripe-all-payments"
    ),
    path(
        "admin/delete-user-financial/<int:user_id>/",
        delete_user_financial_data,
        name="delete_user_financial_data"
    ),

    path(
        "landscaper/pro/monthly-revenue/",
        ProLandscaperMonthlyRevenueView.as_view(),
        name="pro-landscaper-monthly-revenue"
    ),
    path(
        "admin/dashboard/payment-ratio/",
        AdminStripeVsCashDashboardAPIView.as_view(),
        name="stripe-vs-cash-ratio"
    ),
    path("recent-payments/", RecentPaymentsAPIView.as_view(), name="recent-payments"),
    path('client/payment/history/', client_payment_history, name='client-payment-history'),

]
