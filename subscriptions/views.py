
from .models import Plan
from .serializers import PlanSerializer
from django.shortcuts import get_object_or_404
from .models import Subscription, Plan
from .serializers import SubscriptionSerializer

import stripe
from django.conf import settings
from rest_framework import generics, permissions

stripe.api_key = settings.STRIPE_SECRET_KEY
from django.http import JsonResponse
import stripe

from django.views.decorators.csrf import csrf_exempt
# create subscription

# print("strip api key", stripe.api_key )

# def create_subscription(request):
#     plan = request.GET.get("plan")  

#     if plan == "basic":
#         price_id = "price_1SehsEGBPprXqVx5Wxi2VdeL"
#     elif plan == "pro":
#         price_id = "price_1SehssGBPprXqVx5dHqxBncv"
#     else:
#         return JsonResponse({"error": "Invalid plan"}, status=400)

#     session = stripe.checkout.Session.create(
#         mode="subscription",
#         payment_method_types=["card"],
#         line_items=[{
#             "price": price_id,
#             "quantity": 1
#         }],
#         success_url="http://localhost:3000/success",
#         cancel_url="http://localhost:3000/cancel",
#     )

#     return JsonResponse({"checkout_url": session.url})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import stripe
from django.http import HttpResponse
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_subscription(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY  # ✅ must be here

    plan = request.GET.get("plan")
    if plan == "basic":
        price_id = "price_1SehsEGBPprXqVx5Wxi2VdeL"
    elif plan == "pro":
        price_id = "price_1SehssGBPprXqVx5dHqxBncv"
    else:
        return JsonResponse({"error": "Invalid plan"}, status=400)

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="http://localhost:8000/success",
        cancel_url="http://localhost:8000/cancel",
    )
    return JsonResponse({"checkout_url": session.url})

from django.http import HttpResponse

def success(request):
    return HttpResponse("Payment succeeded!")

def cancel(request):
    return HttpResponse("Payment canceled!")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    if endpoint_secret is None:
        return HttpResponse("Webhook secret not configured", status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # handle events
    print("EVENT RECEIVED:", event["type"])
    return HttpResponse(status=200)


class IsAdmin(permissions.BasePermission):
    """Allow only admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"
    


class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        # Save plan in your database first
        plan = serializer.save()

        # Ensure duration is compatible with Stripe
        interval = plan.duration.lower()
        if interval not in ["day", "week", "month", "year"]:
            # Default to month if invalid
            interval = "month"

        # Create product in Stripe
        product = stripe.Product.create(
            name=plan.name,
            description=plan.description or "",
        )

        # Create price in Stripe
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan.price * 100),  # Stripe expects amount in cents
            currency="usd",
            recurring={"interval": interval},  # 'day', 'week', 'month', 'year'
        )

        # Save Stripe IDs in your Plan model
        plan.stripe_product_id = product.id
        plan.stripe_price_id = price.id
        plan.save()


class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdmin()]
        return [permissions.AllowAny()]



class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionCreateView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        plan_id = self.request.data.get("plan")

        plan = get_object_or_404(Plan, id=plan_id)

        serializer.save(user=user, plan=plan)

