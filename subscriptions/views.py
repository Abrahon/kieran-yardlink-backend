import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions
from django.utils import timezone
from datetime import timedelta

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == "POST" else [permissions.AllowAny()]

    def perform_create(self, serializer):
        plan = serializer.save()
        product = stripe.Product.create(name=plan.name)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan.price * 100),
            currency="usd",
            recurring={"interval": "month"},
        )
        plan.stripe_product_id = product.id
        plan.stripe_price_id = price.id
        plan.save()

class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        return [IsAdmin()] if self.request.method in ["PUT", "PATCH", "DELETE"] else [permissions.AllowAny()]

class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

class SubscriptionCreateView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        plan = get_object_or_404(Plan, id=self.request.data.get("plan"))
        serializer.save(user=self.request.user, plan=plan)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session["customer_details"]["email"]
        price_id = session["display_items"][0]["price"]["id"]

        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(email=customer_email)
        plan = Plan.objects.get(stripe_price_id=price_id)

        Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=plan.duration_days),
            status="active"
        )

    return HttpResponse(status=200)

# Optional success/cancel pages
def success(request):
    return HttpResponse("Payment succeeded!")

def cancel(request):
    return HttpResponse("Payment canceled!")
