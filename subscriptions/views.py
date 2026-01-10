import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer,AdminSubscriptionSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework.views import APIView
from django.db.models import Count, Sum
from .models import Plan
from common.permissions import IsLandscaper
from rest_framework import status
from django.db.models import Q
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


# @api_view(["POST"])
# @permission_classes([permissions.IsAuthenticated])
# def create_checkout_session(request):
#     plan_id = request.data.get("plan_id")

#     if not plan_id:
#         return Response(
#             {"detail": "plan_id is required"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     plan = get_object_or_404(Plan, id=plan_id)

#     if not plan.stripe_price_id:
#         return Response(
#             {"detail": "Plan not linked with Stripe"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     session = stripe.checkout.Session.create(
#         mode="subscription",
#         customer_email=request.user.email,
#         metadata={
#             "user_id": str(request.user.id),
#             "plan_id": str(plan.id),
#         },
#         line_items=[{
#             "price": plan.stripe_price_id,
#             "quantity": 1,
#         }],
#         success_url = f"http://localhost:8000/api/success/?session_id={{CHECKOUT_SESSION_ID}}",
#         cancel_url = f"http://localhost:8000/api/cancel/?session_id={{CHECKOUT_SESSION_ID}}"

#     )

#     return Response({"checkout_url": session.url})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    plan_id = request.data.get("plan_id")
    if not plan_id:
        return Response({"detail": "plan_id is required"}, status=400)

    plan = get_object_or_404(Plan, id=plan_id)
    if not plan.stripe_price_id:
        return Response({"detail": "Plan not linked with Stripe"}, status=400)

    # Add session ID to URLs
    success_url = f"http://localhost:8000/api/success/?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"http://localhost:8000/api/cancel/?session_id={{CHECKOUT_SESSION_ID}}"

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=request.user.email,
        metadata={
            "user_id": str(request.user.id),
            "plan_id": str(plan.id),
        },
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return Response({"checkout_url": session.url})




class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsLandscaper]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionCreateView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsLandscaper]

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

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")
        stripe_subscription_id = session.get("subscription")

        if not user_id or not plan_id or not stripe_subscription_id:
            return HttpResponse("Missing metadata", status=400)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(id=user_id).first()
        plan = Plan.objects.filter(id=plan_id).first()

        if not user or not plan:
            return HttpResponse("Invalid user or plan", status=400)

        # ✅ Prevent duplicate subscriptions
        if not Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).exists():
            Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_subscription_id=stripe_subscription_id,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_days),
                status="active"
            )

            # ✅ UPGRADE ROLE
            user.role = "landscaper"
            user.save(update_fields=["role"])

    return HttpResponse(status=200)



# Optional success/cancel pages
from django.http import HttpResponse

def success(request):
    session_id = request.GET.get("session_id")
    if session_id:
        return HttpResponse(f"Payment succeeded! Session ID: {session_id}")
    return HttpResponse("Payment succeeded! (No session ID received)")


def cancel(request):
    session_id = request.GET.get("session_id")
    if session_id:
        return HttpResponse(f"Payment canceled! Session ID: {session_id}")
    return HttpResponse("Payment canceled!")






# add Admin Dashboard Stats API
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




# admin plan delete
class AdminPlanDeleteView(generics.DestroyAPIView):
    queryset = Plan.objects.all()
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_destroy(self, instance):
        # Prevent deleting plans with active subscriptions
        if Subscription.objects.filter(plan=instance, status="active").exists():
            raise ValidationError("Cannot delete plan with active subscriptions.")
        instance.delete()


# admin delete subscriptions
# class AdminSubscriptionDeleteView(generics.DestroyAPIView):
#     queryset = Subscription.objects.all()
#     permission_classes = [IsAuthenticated, IsAdmin]



class AdminSubscriptionDeleteView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, subscription_id):
        # 1️⃣ Get subscription
        subscription = get_object_or_404(Subscription, id=subscription_id)

        # 2️⃣ Cancel Stripe subscription if linked
        if subscription.plan.stripe_price_id:  # optional check
            # If you stored Stripe subscription ID, cancel via API
            stripe_subscription_id = getattr(subscription, 'stripe_subscription_id', None)
            if stripe_subscription_id:
                try:
                    stripe.Subscription.delete(stripe_subscription_id)
                except stripe.error.StripeError as e:
                    return Response(
                        {"detail": f"Stripe error: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # 3️⃣ Update subscription in DB
        subscription.status = "canceled"
        subscription.is_active = False
        subscription.end_date = timezone.now()
        subscription.save(update_fields=["status", "is_active", "end_date"])

        # 4️⃣ Downgrade user role if no other active subscriptions
        user = subscription.user
        active_subs = Subscription.objects.filter(user=user, is_active=True, status="active").exists()
        if not active_subs and user.role == "landscaper":
            user.role = "user"
            user.save(update_fields=["role"])

        return Response(
            {"detail": "Subscription canceled and role updated if necessary."},
            status=status.HTTP_200_OK
        )



# extend subscriptions
class ExtendSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        days = request.data.get("days")

        if not days or int(days) <= 0:
            return Response(
                {"detail": "Valid number of days required"},
                status=400
            )

        subscription = get_object_or_404(Subscription, pk=pk)

        if subscription.end_date < timezone.now():
            subscription.end_date = timezone.now()

        subscription.end_date += timedelta(days=int(days))
        subscription.status = "active"
        subscription.save()

        return Response({
            "message": "Subscription extended successfully",
            "new_end_date": subscription.end_date
        })


# admin subscriptions views list
# views.py
class SubscriptionListAPIView(APIView):
    """
    Admin-only API to list all subscriptions
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        status_param = request.query_params.get("status")       # active / expired / cancelled
        plan_id = request.query_params.get("plan")
        email = request.query_params.get("email")

        queryset = Subscription.objects.select_related(
            "user", "plan"
        ).order_by("-created_at")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)

        if email:
            queryset = queryset.filter(user__email__icontains=email)

        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "count": queryset.count(),
                "subscriptions": serializer.data,
            },
            status=status.HTTP_200_OK
        )

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def confirm_subscription(request):
    session_id = request.query_params.get("session_id")
    if not session_id:
        return Response({"detail": "session_id is required"}, status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        return Response({"detail": "Invalid session"}, status=400)

    if session.payment_status == "paid" and session.status == "complete":
        plan_id = session.metadata.get("plan_id")
        plan = Plan.objects.filter(id=plan_id).first()
        user = request.user

        if not plan:
            return Response({"detail": "Plan not found"}, status=404)

        # Create subscription if not exists
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            plan=plan,
            defaults={
                "stripe_subscription_id": session.subscription,
                "status": "active",
                "start_date": timezone.now(),
                "end_date": timezone.now() + timedelta(days=plan.duration_days),
                "is_active": True,
            }
        )

        # Upgrade user role if not already
        if user.role != "landscaper":
            user.role = "landscaper"
            user.save(update_fields=["role"])

        return Response({
            "paid": True,
            "detail": "Subscription activated",
            "plan": {
                "id": plan.id,
                "name": plan.name,           # Basic or Pro
                "price": float(plan.price),
                "discount": float(plan.discount),
                "duration": plan.duration,
                "final_price": float(plan.price - (plan.price * plan.discount / 100))
            },
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "remaining_days": (subscription.end_date - timezone.now()).days
            }
        }, status=200)

    return Response({"paid": False, "detail": "Payment not completed"}, status=200)
