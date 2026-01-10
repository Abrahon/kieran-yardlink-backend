from django.urls import path
from .import views

urlpatterns = [
    path("plans/", views.PlanListCreateView.as_view(), name="plan-list-create"),
    path("plans/<int:pk>/", views.PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),

    path("subscriptions/", views.SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/create/", views.SubscriptionCreateView.as_view(), name="subscription-create"),

    path("subscriptions/checkout/", views.create_checkout_session, name="stripe-checkout"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),

    path("success/", views.success, name="payment-success"),
    path("cancel/", views.cancel, name="payment-cancel"),

    # admin dashyboard
    path("admin/dashboard-stats/", views.AdminDashboardStatsView.as_view()),
    path("admin/plans/<int:pk>/delete/", views.AdminPlanDeleteView.as_view()),
    path("admin/subscriptions/<int:pk>/delete/", views.AdminSubscriptionDeleteView.as_view()),
    path("admin/subscriptions/<int:pk>/extend/", views.ExtendSubscriptionView.as_view()),
    path("admin/subscriptions/",views.SubscriptionListAPIView.as_view(),name="admin-subscriptions"),
    path("confirm-subscription/", views.confirm_subscription, name="confirm-subscription"),





]
