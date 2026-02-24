import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions
from django.http import HttpResponse
from .serializers import PlanSerializer, SubscriptionSerializer,AdminSubscriptionSerializer,SubscriptionUpgradeSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Sum
from .models import Plan
from common.permissions import IsLandscaper
from rest_framework import status
from django.db.models import Q
stripe.api_key = settings.STRIPE_SECRET_KEY
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionSerializer
from common.permissions import IsAdmin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import stripe
from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()






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



from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404

import stripe
from django.conf import settings
from .models import Plan, Subscription
from django.contrib.auth import get_user_model

User = get_user_model()


# ================================================
# Helper: safe start/end dates
# ================================================
def safe_subscription_dates(stripe_sub, plan=None):
    """
    Returns start and end datetimes for subscription.
    Falls back to timezone.now() and plan duration if Stripe fields are missing.
    """
    start_ts = stripe_sub.get("current_period_start")
    end_ts = stripe_sub.get("current_period_end")

    start = timezone.make_aware(datetime.fromtimestamp(start_ts)) if start_ts else timezone.now()

    if end_ts:
        end = timezone.make_aware(datetime.fromtimestamp(end_ts))
    elif plan:
        end = start + timedelta(days=plan.duration_days)
    else:
        end = start + timedelta(days=30)  # default fallback

    return start, end


# ================================================
# Create Checkout Session
# ================================================
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    plan_id = request.data.get("plan_id")
    if not plan_id:
        return Response({"detail": "plan_id is required"}, status=400)

    plan = get_object_or_404(Plan, id=plan_id)

    if not plan.stripe_price_id:
        return Response({"detail": "Plan not linked with Stripe"}, status=400)

    # CREATE OR REUSE STRIPE CUSTOMER
    if not request.user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=request.user.email,
            name=request.user.name or request.user.email,
        )
        request.user.stripe_customer_id = customer.id
        request.user.save(update_fields=["stripe_customer_id"])

    success_url = "https://zznkjkkp-8000.inc1.devtunnels.ms/api/success/?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "https://zznkjkkp-8000.inc1.devtunnels.ms/api/cancel/"

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=request.user.stripe_customer_id,
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        subscription_data={
            "trial_period_days": 14,
            "metadata": {
                "user_id": str(request.user.id),
                "plan_id": str(plan.id),
            }
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return Response({"checkout_url": session.url})


# ================================================
# Stripe Webhook
# ================================================
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

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

    event_type = event["type"]

    # ================================================
    # 1️⃣ CHECKOUT SESSION COMPLETED
    # ================================================
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        subscription_id = session.get("subscription")

        if not subscription_id:
            return HttpResponse(status=200)

        stripe_sub = stripe.Subscription.retrieve(subscription_id)
        metadata = stripe_sub.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")

        if not user_id or not plan_id:
            return HttpResponse(status=200)

        try:
            user = User.objects.get(id=user_id)
            plan = Plan.objects.get(id=plan_id)
        except (User.DoesNotExist, Plan.DoesNotExist):
            return HttpResponse(status=200)

        start, end = safe_subscription_dates(stripe_sub, plan)

        Subscription.objects.update_or_create(
            stripe_subscription_id=subscription_id,
            defaults={
                "user": user,
                "plan": plan,
                "stripe_customer_id": stripe_sub.customer,
                "status": stripe_sub.status,
                "is_active": stripe_sub.status in ["trialing", "active"],
                "is_trial": stripe_sub.status == "trialing",
                "start_date": start,
                "end_date": end,
            }
        )

        # Upgrade user role
        if user.role != "landscaper":
            user.role = "landscaper"
            user.save(update_fields=["role"])

    # ================================================
    # 2️⃣ INVOICE PAYMENT SUCCEEDED
    # ================================================
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return HttpResponse(status=200)

        stripe_sub = stripe.Subscription.retrieve(subscription_id)

        subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
        plan = subscription.plan if subscription else None

        start, end = safe_subscription_dates(stripe_sub, plan)

        Subscription.objects.filter(stripe_subscription_id=subscription_id).update(
            status=stripe_sub.status,
            is_active=stripe_sub.status == "active",
            is_trial=False,
            start_date=start,
            end_date=end,
        )

    # ================================================
    # 3️⃣ PAYMENT FAILED
    # ================================================
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        if subscription_id:
            Subscription.objects.filter(stripe_subscription_id=subscription_id).update(
                status="past_due",
                is_active=False,
                is_trial=False
            )

    # ================================================
    # 4️⃣ SUBSCRIPTION UPDATED
    # ================================================
    elif event_type == "customer.subscription.updated":
        stripe_sub = event["data"]["object"]
        subscription_id = stripe_sub["id"]

        subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
        plan = subscription.plan if subscription else None

        start, end = safe_subscription_dates(stripe_sub, plan)

        Subscription.objects.filter(stripe_subscription_id=subscription_id).update(
            status=stripe_sub["status"],
            is_active=stripe_sub["status"] in ["trialing", "active"],
            is_trial=stripe_sub["status"] == "trialing",
            start_date=start,
            end_date=end,
        )

    # ================================================
    # 5️⃣ SUBSCRIPTION CANCELED
    # ================================================
    elif event_type == "customer.subscription.deleted":
        stripe_sub = event["data"]["object"]
        Subscription.objects.filter(stripe_subscription_id=stripe_sub["id"]).update(
            status="canceled",
            is_active=False,
            is_trial=False
        )

    return HttpResponse(status=200)




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
        print()
        serializer.save(user=self.request.user, plan=plan)



from rest_framework.permissions import IsAdminUser

class AdminPauseSubscriptionAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, subscription_id):
        """
        Admin can pause/resume a subscription.
        PATCH body: {"is_active": false} → pause
                    {"is_active": true} → resume
        Response includes plan_name, plan_price, and subscription details.
        """
        subscription = get_object_or_404(Subscription, id=subscription_id)

        # Update is_active field
        is_active = request.data.get("is_active")
        if is_active is None:
            return Response({"detail": "is_active field is required"}, status=status.HTTP_400_BAD_REQUEST)

        subscription.is_active = bool(is_active)
        subscription.save(update_fields=["is_active"])

        message = "Subscription paused successfully" if not subscription.is_active else "Subscription resumed successfully"

        serializer = SubscriptionUpgradeSerializer(subscription)

        return Response({
            "status": "success",
            "message": message,
            "subscription": serializer.data
        }, status=status.HTTP_200_OK)


# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

#     try:
#         event = stripe.Webhook.construct_event(
#             payload,
#             sig_header,
#             settings.STRIPE_WEBHOOK_SECRET
#         )
#     except stripe.error.SignatureVerificationError:
#         return HttpResponse(status=400)
#     except Exception:
#         return HttpResponse(status=400)

#     event_type = event["type"]

#     def safe_dt(ts):
#         return timezone.make_aware(datetime.fromtimestamp(ts)) if ts else None

#     # 1️⃣ Checkout session completed
#     if event_type == "checkout.session.completed":
#         session = event["data"]["object"]
#         subscription_id = session.get("subscription")
#         if subscription_id:
#             stripe_sub = stripe.Subscription.retrieve(subscription_id)
#             metadata = stripe_sub.get("metadata", {})

#             user_id = metadata.get("user_id")
#             plan_id = metadata.get("plan_id")

#             if not user_id or not plan_id:
#                 return HttpResponse(status=200)

#             try:
#                 user = User.objects.get(id=user_id)
#                 plan = Plan.objects.get(id=plan_id)
#             except (User.DoesNotExist, Plan.DoesNotExist):
#                 return HttpResponse(status=200)

#             Subscription.objects.update_or_create(
#                 stripe_subscription_id=subscription_id,
#                 defaults={
#                     "user": user,
#                     "plan": plan,
#                     "stripe_customer_id": stripe_sub.customer,
#                     "status": stripe_sub.status,
#                     "is_active": stripe_sub.status in ["trialing", "active"],
#                     "is_trial": stripe_sub.status == "trialing",
#                     "start_date": safe_dt(stripe_sub.get("current_period_start")),
#                     "end_date": safe_dt(stripe_sub.get("current_period_end")),
#                 }
#             )

#             if user.role != "landscaper":
#                 user.role = "landscaper"
#                 user.save(update_fields=["role"])

#     # 2️⃣ Invoice succeeded
#     elif event_type == "invoice.payment_succeeded":
#         invoice = event["data"]["object"]
#         subscription_id = invoice.get("subscription")
#         if subscription_id:
#             stripe_sub = stripe.Subscription.retrieve(subscription_id)
#             Subscription.objects.filter(
#                 stripe_subscription_id=subscription_id
#             ).update(
#                 status=stripe_sub.status,
#                 is_active=stripe_sub.status == "active",
#                 is_trial=False,
#                 start_date=safe_dt(stripe_sub.get("current_period_start")),
#                 end_date=safe_dt(stripe_sub.get("current_period_end")),
#             )

#     # 3️⃣ Payment failed
#     elif event_type == "invoice.payment_failed":
#         invoice = event["data"]["object"]
#         subscription_id = invoice.get("subscription")
#         if subscription_id:
#             Subscription.objects.filter(
#                 stripe_subscription_id=subscription_id
#             ).update(
#                 status="past_due",
#                 is_active=False,
#                 is_trial=False
#             )

#     # 4️⃣ Subscription updated
#     elif event_type == "customer.subscription.updated":
#         stripe_sub = event["data"]["object"]
#         subscription_id = stripe_sub["id"]

#         Subscription.objects.filter(
#             stripe_subscription_id=subscription_id
#         ).update(
#             status=stripe_sub["status"],
#             is_active=stripe_sub["status"] in ["trialing", "active"],
#             is_trial=stripe_sub["status"] == "trialing",
#             start_date=safe_dt(stripe_sub.get("current_period_start")),
#             end_date=safe_dt(stripe_sub.get("current_period_end")),
#         )

#     # 5️⃣ Subscription canceled
#     elif event_type == "customer.subscription.deleted":
#         stripe_sub = event["data"]["object"]
#         Subscription.objects.filter(
#             stripe_subscription_id=stripe_sub["id"]
#         ).update(
#             status="canceled",
#             is_active=False,
#             is_trial=False
#         )

#     return HttpResponse(status=200)

# # ----------------------------
# # CREATE STRIPE CHECKOUT SESSION
# # ----------------------------
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def create_checkout_session(request):
#     plan_id = request.data.get("plan_id")
#     if not plan_id:
#         return Response({"detail": "plan_id is required"}, status=400)

#     plan = get_object_or_404(Plan, id=plan_id)
#     if not plan.stripe_price_id:
#         return Response({"detail": "Plan not linked with Stripe"}, status=400)

#     # Create or reuse Stripe customer
#     if not request.user.stripe_customer_id:
#         customer = stripe.Customer.create(
#             email=request.user.email,
#             name=request.user.name or request.user.email
#         )
#         request.user.stripe_customer_id = customer.id
#         request.user.save(update_fields=["stripe_customer_id"])

#     success_url = "https://example.com/success/?session_id={CHECKOUT_SESSION_ID}"
#     cancel_url = "https://example.com/cancel/"

#     session = stripe.checkout.Session.create(
#         mode="subscription",
#         customer=request.user.stripe_customer_id,
#         line_items=[{
#             "price": plan.stripe_price_id,
#             "quantity": 1
#         }],
#         subscription_data={
#             "trial_period_days": 14,
#             "metadata": {
#                 "user_id": str(request.user.id),
#                 "plan_id": str(plan.id)
#             }
#         },
#         success_url=success_url,
#         cancel_url=cancel_url
#     )

#     return Response({"checkout_url": session.url})


# Optional success/cancel pages
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
        # Prevent deleting a plan with active subscriptions
        if Subscription.objects.filter(plan=instance, status="active").exists():
            raise ValidationError({
                "detail": "Cannot delete plan with active subscriptions."
            })
        # Delete the plan
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Plan deleted successfully."},
            status=status.HTTP_200_OK
        )

# subscriptions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
import stripe

from .models import Subscription, SubscriptionStatus
from profiles.models import LandscaperProfilies



class AdminSubscriptionDeleteView(APIView):
    """
    Admin API to cancel/delete any user's subscription safely.
    If the subscription does not exist on Stripe, it continues and only updates the DB.
    """
    permission_classes = [IsAdmin]

    def delete(self, request, subscription_id):
        # 1️⃣ Get the subscription object
        subscription = get_object_or_404(Subscription, id=subscription_id)

        # 2️⃣ Cancel Stripe subscription if ID exists
        stripe_subscription_id = subscription.stripe_subscription_id
        if stripe_subscription_id:
            try:
                stripe.Subscription.delete(stripe_subscription_id)
            except stripe.error.InvalidRequestError as e:
                if "No such subscription" in str(e):
                    # Stripe subscription not found, just log and continue
                    print(f"[Stripe] Subscription not found: {stripe_subscription_id}")
                else:
                    return Response(
                        {"detail": f"Stripe error: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # 3️ Update subscription in DB
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.is_active = False
        subscription.end_date = timezone.now()
        subscription.save(update_fields=["status", "is_active", "end_date"])

        # 4️⃣ Check if user has other active subscriptions
        user = subscription.user
        has_active = Subscription.objects.filter(
            user=user,
            status=SubscriptionStatus.ACTIVE,
            is_active=True
        ).exists()

        # 5️⃣ Downgrade landscaper profile if no active subscriptions
        profile = LandscaperProfilies.objects.filter(user=user).first()
        if profile and not has_active:
            # profile.plan = LandscaperProfilies.BASIC
            profile.save(update_fields=["plan"])

        return Response(
            {
                "detail": "Subscription cancelled and landscaper downgraded if no active plan",
                "subscription_status": subscription.status,
                "plan_after_cancellation": profile.plan if profile else "N/A"
            },
            status=status.HTTP_200_OK
        )



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

        # If expired, restart from today
        base_date = (
            subscription.end_date
            if subscription.end_date > timezone.now()
            else timezone.now()
        )

        subscription.end_date = base_date + timedelta(days=int(days))
        subscription.is_trial = False 
        subscription.status = "active"
        subscription.is_active = True
        subscription.save()

        return Response({
            "message": "Subscription extended successfully",
            "subscription_id": subscription.id,
            "new_end_date": subscription.end_date,
            "remaining_days": (subscription.end_date - timezone.now()).days
        })


# admin subscriptions views list
# views.py

# subscriptions/views.py
class SubscriptionListAPIView(APIView):
    """
    Admin-only API to list subscriptions with:
    - search: plan name, user email, or user full name
    - filter by plan (partial match): e.g., 'ProPlan' or 'BasicPlan'
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        search = request.query_params.get("search", "") 
        plan_name = request.query_params.get("plan", "")  

        queryset = Subscription.objects.select_related("user", "plan").order_by("-created_at")

        # Flexible plan filter (partial match)
        if plan_name:
            queryset = queryset.filter(plan__name__icontains=plan_name)

        # Apply search filter (plan name, user email, or user name)
        if search:
            queryset = queryset.filter(
                Q(plan__name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__name__icontains=search)
            )

        serializer = SubscriptionSerializer(queryset, many=True, context={"request": request})

        return Response({
            "count": queryset.count(),
            "subscriptions": serializer.data,
        }, status=status.HTTP_200_OK)


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





class MySubscriptionAPIView(APIView):
    """
    API to view the logged-in user's subscriptions,
    including auto-renew status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all subscriptions for this user, latest first
        queryset = Subscription.objects.select_related("user", "plan").filter(
            user=request.user
        ).order_by("-created_at")

        # Serialize subscriptions
        serializer = SubscriptionSerializer(queryset, many=True, context={"request": request})

        # Build response including auto_renew
        subscriptions_data = []
        for sub, ser_data in zip(queryset, serializer.data):
            subscriptions_data.append({
                **ser_data,
                "auto_renew": sub.auto_renew,  # add auto_renew field
                "is_trial": sub.is_trial,      # optional, useful to show trial status
                "current_end_date": sub.end_date
            })

        return Response({
            "count": queryset.count(),
            "subscriptions": subscriptions_data
        }, status=status.HTTP_200_OK)
        
# # stripe onfo get
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response


# subscriptions/views.py
class CancelOwnSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, subscription_id):
        """
        Cancel or remove user's subscription.
        Works for trial, active paid, or inactive subscriptions.
        """
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=request.user)
        except Subscription.DoesNotExist:
            return Response(
                {"detail": "Subscription not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only cancel if not already cancelled/removed
        if subscription.status == "cancelled":
            return Response(
                {"detail": "Subscription already cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update subscription status to cancelled
        subscription.status = "cancelled"
        subscription.save(update_fields=["status"])

        return Response(
            {
                "detail": f"Subscription {subscription.id} has been cancelled successfully.",
                "subscription_status": subscription.status
            },
            status=status.HTTP_200_OK
        )


class ToggleAutoRenewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, subscription_id):
        """
        Toggle auto-renewal for a paid subscription.
        - Trial subscriptions cannot be auto-renewed.
        - Next renewal will extend subscription for full plan duration.
        """
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=request.user)
        except Subscription.DoesNotExist:
            return Response({"detail": "Subscription not found."}, status=404)

        if subscription.is_trial:
            return Response({"detail": "Trial subscriptions cannot be auto-renewed."}, status=400)

        # auto_renew field must be provided
        auto_renew = request.data.get("auto_renew")
        if auto_renew is None:
            return Response({"detail": "auto_renew field is required."}, status=400)

        # Update subscription auto_renew flag
        subscription.auto_renew = bool(auto_renew)
        subscription.save(update_fields=["auto_renew"])

        return Response({
            "subscription_id": subscription.id,
            "plan_name": subscription.plan.name,
            "auto_renew": subscription.auto_renew,
            "current_end_date": subscription.end_date
        })

# subscription ratio

from rest_framework.permissions import IsAdminUser

from subscriptions.models import Subscription, SubscriptionStatus
from django.db.models import Count

class SubscriptionRatioAPIView(APIView):
    """
    Returns the subscription ratio between Pro and Basic plans as percentage.
    Only counts ACTIVE subscriptions.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Count active subscriptions per plan
        subscriptions = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE)
        plan_counts = subscriptions.values('plan__name').annotate(count=Count('id'))

        # Initialize counts
        basic_count = 0
        pro_count = 0
        total = 0

        # Map counts
        for item in plan_counts:
            plan_name = item['plan__name'].lower()
            count = item['count']
            total += count
            if plan_name == 'basic':
                basic_count = count
            elif plan_name == 'pro':
                pro_count = count

        # Avoid division by zero
        if total == 0:
            basic_percentage = 0
            pro_percentage = 0
        else:
            basic_percentage = round((basic_count / total) * 100, 2)
            pro_percentage = round((pro_count / total) * 100, 2)

        return Response({
            "total_active_subscriptions": total,
            "basic": {
                "count": basic_count,
                "percentage": basic_percentage
            },
            "pro": {
                "count": pro_count,
                "percentage": pro_percentage
            }
        })



class UpgradePlanAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Get user's current active subscription
        subscription = get_object_or_404(Subscription, user=user, is_active=True)

        # Check if user is already on pro
        if subscription.plan.name.lower() == "pro":
            return Response({"detail": "You are already on Pro plan"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the "Pro" plan
        pro_plan = get_object_or_404(Plan, name__iexact="pro")

        # Upgrade subscription
        subscription.plan = pro_plan
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=pro_plan.duration_days)
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.is_trial = False  # if any trial
        subscription.save()

        serializer = SubscriptionUpgradeSerializer(subscription)
        return Response({
            "detail": "Subscription upgraded to Pro successfully",
            "subscription": serializer.data
        }, status=status.HTTP_200_OK)