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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView
from django.db.models import Count, Sum
from .models import Plan

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




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    plan_id = request.data.get("plan_id")

    if not plan_id:
        return JsonResponse(
            {"error": "plan_id is required"},
            status=400
        )

    plan = get_object_or_404(Plan, id=plan_id)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=request.user.email,
        line_items=[
            {
                "price": plan.stripe_price_id,
                "quantity": 1,
            }
        ],
        success_url="http://127.0.0.1:8000/api/success/",
        cancel_url="http://127.0.0.1:8000/api/cancel/",
    )

    return JsonResponse({"checkout_url": session.url})

# its for optional
# stripe.checkout.Session.create(
#     mode="subscription",
#     customer_email=request.user.email,
#     line_items=[
#         {
#             "price": plan.stripe_price_id,
#             "quantity": 1,
#         }
#     ],
#     success_url="http://localhost:8000/api/success/",
#     cancel_url="http://localhost:8000/api/cancel/",
#     metadata={
#         "price_id": plan.stripe_price_id
#     }
# )


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

    if not sig_header:
        return HttpResponse("Missing signature", status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)
    except Exception:
        return HttpResponse("Webhook error", status=400)

    # ✅ Handle successful checkout
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        customer_email = session.get("customer_details", {}).get("email")
        stripe_price_id = session["metadata"].get("price_id")

        if not customer_email or not stripe_price_id:
            return HttpResponse("Missing metadata", status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(email=customer_email).first()
        plan = Plan.objects.filter(stripe_price_id=stripe_price_id).first()

        if user and plan:
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


# add total subscription


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1)

        total_plans = Plan.objects.count()

        active_subscriptions = Subscription.objects.filter(
            status="active",
            end_date__gte=now
        ).count()

        expired_subscriptions = Subscription.objects.filter(
            end_date__lt=now
        ).count()

        # Monthly revenue (DB-based, Stripe-safe)
        monthly_revenue = Subscription.objects.filter(
            start_date__gte=month_start,
            status="active"
        ).aggregate(
            total=Sum("plan__price")
        )["total"] or 0

        subscribers_by_plan = (
            Subscription.objects.filter(status="active")
            .values("plan__name")
            .annotate(total=Count("id"))
        )

        return Response({
            "total_plans": total_plans,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "monthly_revenue": monthly_revenue,
            "subscribers_by_plan": subscribers_by_plan
        })
