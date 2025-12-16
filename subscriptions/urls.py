# from django.urls import path

# from .views import PlanListCreateView,PlanRetrieveUpdateDeleteView,SubscriptionListView,SubscriptionCreateView,create_subscription,stripe_webhook,success,cancel

# urlpatterns = [
#     # Plan routes
#     path("plans/", PlanListCreateView.as_view(), name="plan-list-create"),
#     path("plans/<int:pk>/", PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),

#     # Subscription routes
#     path("subscriptions/", SubscriptionListView.as_view(), name="subscription-list"),
#     path("subscriptions/create/", SubscriptionCreateView.as_view(), name="subscription-create"),
#     path("create-subscription/", create_subscription),
#     path("stripe/webhook/", stripe_webhook),
#     path("success/", success),
#     path("cancel/", cancel),

# ]

from django.urls import path
from .views import (
    PlanListCreateView, PlanRetrieveUpdateDeleteView,
    SubscriptionListView, SubscriptionCreateView,
    create_subscription, stripe_webhook,
    success, cancel
)

urlpatterns = [
    # Plan routes
    path("plans/", PlanListCreateView.as_view(), name="plan-list-create"),
    path("plans/<int:pk>/", PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),

    # Subscription routes
    path("subscriptions/", SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/create/", SubscriptionCreateView.as_view(), name="subscription-create"),

    # Stripe routes
    path("create-subscription/", create_subscription, name="create-subscription"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    path("success/", success, name="payment-success"),
    path("cancel/", cancel, name="payment-cancel"),
]
