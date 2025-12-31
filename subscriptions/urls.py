from django.urls import path
from . import views

urlpatterns = [
    path("plans/", views.PlanListCreateView.as_view(), name="plan-list-create"),
    path("plans/<int:pk>/", views.PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),
    path("subscriptions/", views.SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/create/", views.SubscriptionCreateView.as_view(), name="subscription-create"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("success/", views.success, name="payment-success"),
    path("cancel/", views.cancel, name="payment-cancel"),
]
