
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, F, FloatField
from .serializers import PaymentHistorySerializer
from datetime import datetime
from profiles.models import LandscaperProfilies
from services.models import ServiceSchedule, PaymentStatus
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate
from rest_framework.permissions import IsAdminUser
from subscriptions.models import Subscription
from subscriptions.enums import SubscriptionStatus
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.shortcuts import get_object_or_404
from common.permissions import IsClient,IsLandscaper

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from services.models import ServiceSchedule, PaymentStatus
from profiles.models import LandscaperProfilies
from payments.serializers import PaymentHistorySerializer
from django.db.models import Sum, F
from rest_framework.response import Response
from services.models import ServiceSchedule, PaymentStatus
from profiles.models import LandscaperProfilies
from django.db.models import F, FloatField, Value, Sum
from django.db.models.functions import Coalesce, Cast
from django.utils.timezone import now
from profiles.models import LandscaperProfilies
from services.models import ServiceSchedule, PaymentStatus
from rest_framework.views import APIView
from profiles.models import ClientProfile
from datetime import datetime, timedelta
from django.db.models import Sum, FloatField, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from services.models import ServiceSchedule, PaymentStatus
from profiles.models import ClientProfile
from rest_framework.permissions import IsAdminUser
from subscriptions.models import Subscription, SubscriptionStatus
from .serializers import PaymentHistorySerializer 
import csv
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from common.permissions import IsProLandscaper
from common.permissions import IsProLandscaper
from django.db.models import Sum, F, FloatField, Value
from django.db.models.functions import TruncMonth
from rest_framework.response import Response
from rest_framework.views import APIView
from profiles.models import LandscaperProfilies
from services.models import ServiceSchedule, PaymentStatus
from datetime import datetime
from collections import OrderedDict
from calendar import monthrange



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_checkout_session(request):
    """
    Client pays for completed job.
    If client already paid this landscaper before,
    new jobs auto-mark as PAID.
    """

    import stripe
    from django.conf import settings

    schedule_id = request.data.get("schedule_id")
    if not schedule_id:
        return Response({"error": "schedule_id is required"}, status=400)

    try:
        schedule = ServiceSchedule.objects.get(
            id=schedule_id,
            client=request.user.clientprofile
        )
    except ServiceSchedule.DoesNotExist:
        return Response({"error": "Schedule not found"}, status=404)

    if not schedule.is_completed:
        return Response({"error": "Job is not completed yet"}, status=400)

    if schedule.payment_status == PaymentStatus.PAID:
        return Response({"message": "Already paid"}, status=200)

    #  AUTO-PAY CHECK
    already_paid_before = ServiceSchedule.objects.filter(
        client=schedule.client,
        landscaper=schedule.landscaper,
        payment_status=PaymentStatus.PAID
    ).exists()

    if already_paid_before:
        schedule.payment_status = PaymentStatus.PAID
        schedule.save(update_fields=["payment_status"])

        return Response({
            "message": "Auto-paid (existing trusted landscaper)",
            "payment_status": schedule.payment_status
        })

    # ------------------------------
    # If no previous payment → create Stripe checkout
    # ------------------------------

    amount = int(schedule.service.price * 100)
    total_amount = amount + int(amount * 0.02)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=schedule.client.user.email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": total_amount,
                    "product_data": {
                        "name": f"{schedule.service.name} (Job ID {schedule.id})",
                        "description": f"Completed by: {schedule.landscaper.user.name}"
                    },
                },
                "quantity": 1,
            }],
            success_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/success/?schedule_id={schedule.id}",
            cancel_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/cancel/?schedule_id={schedule.id}",
            metadata={
                "schedule_id": str(schedule.id),
                "landscaper_id": str(schedule.landscaper.id)
            }
        )
    except stripe.error.StripeError as e:
        return Response({"error": str(e)}, status=500)

    schedule.payment_status = PaymentStatus.PENDING
    schedule.stripe_payment_id = session.id
    schedule.save(update_fields=["payment_status", "stripe_payment_id"])

    return Response({"checkout_url": session.url})


# Success / Cancel Endpoints
@api_view(["GET"])
def payment_success(request):
    schedule_id = request.GET.get("schedule_id")
    return Response({"message": "Payment successful", "schedule_id": schedule_id})


@api_view(["GET"])
def payment_cancel(request):
    schedule_id = request.GET.get("schedule_id")
    return Response({"message": "Payment cancelled", "schedule_id": schedule_id})




class CashPaymentScheduleAPIView(APIView):
    """
    Client selects cash payment for a completed job.
    Sends email to landscaper.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id):
        # 1️⃣ Get the schedule for this client
        client_profile = getattr(request.user, "clientprofile", None)
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id, client=client_profile)

        # 2️⃣ Check if job is completed
        if not schedule.is_completed:
            return Response({"error": "Job not completed yet"}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ Check if already paid
        if schedule.payment_status == PaymentStatus.PAID:
            return Response({"error": "Already paid"}, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ Mark cash pending
        schedule.payment_status = PaymentStatus.CASH_PENDING
        schedule.save(update_fields=["payment_status"])

        # 5️⃣ Notify landscaper via email (simplest example)
        landscaper_email = schedule.landscaper.user.email
        send_mail(
            subject=f"Cash Payment Pending for Service {schedule.service.name}",
            message=f"Client {client_profile.name} has selected cash payment for the service scheduled on {schedule.scheduled_date} at {schedule.scheduled_time}. Please confirm when received.",
            from_email="no-reply@yardlink.com",
            recipient_list=[landscaper_email],
        )

        return Response({
            "message": "Cash payment selected. Landscaper notified.",
            "payment_status": schedule.payment_status
        })


class ConfirmCashPaymentAPIView(APIView):
    """
    Landscaper confirms if payment is received or not
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id):
        # 1️⃣ Get the schedule for this landscaper
        landscaper_profile = getattr(request.user, "landscaperprofilies", None)
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id, landscaper=landscaper_profile)

        # 2️⃣ Check if job is completed and payment is cash pending
        if not schedule.is_completed or schedule.payment_status != PaymentStatus.CASH_PENDING:
            return Response({"error": "Cannot confirm payment for this schedule"}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ Get confirmation from request
        received = request.data.get("received")
        if received not in [True, False]:
            return Response({"error": "Provide 'received': true or false"}, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ Update payment status
        schedule.payment_status = PaymentStatus.PAID if received else PaymentStatus.CASH_PENDING
        schedule.save(update_fields=["payment_status"])

        return Response({
            "message": "Payment updated successfully",
            "payment_status": schedule.payment_status
        })


@csrf_exempt
def stripe_webhook(request):
    """
    Stripe webhook for handling checkout.session.completed.
    Always returns 200 to Stripe to prevent retries.
    Logs all events for debugging.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    if sig_header is None:
        print("[Webhook] Missing Stripe signature header")
        return HttpResponse(status=200)  # Always return 200

    try:
        # Construct the event
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print(f"[Webhook] Invalid payload: {e}")
        return HttpResponse(status=200)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"[Webhook] Invalid signature: {e}")
        return HttpResponse(status=200)
    except Exception as e:
        print(f"[Webhook] Unknown error: {e}")
        return HttpResponse(status=200)

    # Log all events for debugging
    print(f"[Webhook] Event received: {event['type']}")

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        schedule_id = metadata.get("schedule_id")

        if schedule_id:
            try:
                schedule = ServiceSchedule.objects.get(id=schedule_id)
                schedule.payment_status = PaymentStatus.PAID
                schedule.stripe_payment_id = session.get("id")
                schedule.save(update_fields=["payment_status", "stripe_payment_id"])
                print(f"[Webhook] Schedule {schedule_id} marked as PAID")
            except ServiceSchedule.DoesNotExist:
                print(f"[Webhook] Schedule {schedule_id} not found")
                # Do not fail webhook; just log

    # Optional: log other event types for debugging
    else:
        print(f"[Webhook] Ignored event type: {event['type']}")

    # Always return 200 to Stripe
    return HttpResponse(status=200)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def landscaper_payment_history(request):
    """
    Returns landscaper payment history with revenue summary:
    - monthly_paid / monthly_pending
    - yearly_paid / yearly_pending
    - total_paid / total_pending
    Each job includes total_amount = service price * 1.02
    """
    user = request.user

    # Get landscaper profile
    try:
        landscaper = user.landscaperprofilies
    except LandscaperProfilies.DoesNotExist:
        return Response({"error": "No landscaper profile found"}, status=404)

    # All completed jobs for this landscaper
    schedules = ServiceSchedule.objects.filter(
        landscaper=landscaper,
        is_completed=True
    ).select_related('client', 'service').order_by('-scheduled_date')

    # Annotate each job with paid_amount (price * 1.02)
    schedules = schedules.annotate(
        paid_amount=Cast(F('service__price'), FloatField()) * Value(1.02, output_field=FloatField())
    )

    # Serialize payment history
    serializer = PaymentHistorySerializer(schedules, many=True)

    # Get current date
    today = now()
    current_month = today.month
    current_year = today.year

    # Monthly revenue
    monthly_jobs = schedules.filter(scheduled_date__year=current_year, scheduled_date__month=current_month)
    monthly_paid = monthly_jobs.filter(payment_status=PaymentStatus.PAID).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']
    monthly_pending = monthly_jobs.filter(payment_status=PaymentStatus.PENDING).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']

    # Yearly revenue
    yearly_jobs = schedules.filter(scheduled_date__year=current_year)
    yearly_paid = yearly_jobs.filter(payment_status=PaymentStatus.PAID).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']
    yearly_pending = yearly_jobs.filter(payment_status=PaymentStatus.PENDING).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']

    # Total revenue (all time)
    total_paid = schedules.filter(payment_status=PaymentStatus.PAID).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']
    total_pending = schedules.filter(payment_status=PaymentStatus.PENDING).aggregate(
        total=Coalesce(Sum('paid_amount'), 0.0)
    )['total']

    # Return response
    return Response({
        "payment_history": serializer.data,
        "revenue_summary": {
            "monthly_paid": round(monthly_paid, 2),
            "monthly_pending": round(monthly_pending, 2),
            "yearly_paid": round(yearly_paid, 2),
            "yearly_pending": round(yearly_pending, 2),
            "total_paid": round(total_paid, 2),
            "total_pending": round(total_pending, 2)
        }
    })




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def client_payment_history(request):
    """
    Client view:
    - Shows all landscapers the client worked with
    - Each landscaper includes:
        - name, email
        - completed services
        - property/location
        - date of completed job
        - total jobs worked for this client
        - total amount paid to this landscaper
    """
    client = request.user.clientprofile

    # Completed jobs for this client
    jobs = ServiceSchedule.objects.filter(
        client=client,
        is_completed=True
    ).select_related("landscaper", "service").order_by("-completed_at")

    # Group jobs by landscaper
    landscaper_dict = {}
    for job in jobs:
        landscaper_id = job.landscaper.id
        if landscaper_id not in landscaper_dict:
            landscaper_dict[landscaper_id] = {
                "landscaper_id": landscaper_id,
                "landscaper_name": job.landscaper.user.name,
                "landscaper_email": job.landscaper.user.email,
                "jobs_count": 0,
                "total_amount": 0.0,
                "jobs": []
            }

        # Add job info
        job_amount = float(job.service.price or 0)  # price in USD
        landscaper_dict[landscaper_id]["jobs"].append({
            "service_name": job.service.name,
            "property_address": getattr(job.client.user.properties.first(), "address", ""),
            "completed_at": job.completed_at.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": round(job_amount, 2)
        })

        # Update count and total amount
        landscaper_dict[landscaper_id]["jobs_count"] += 1
        landscaper_dict[landscaper_id]["total_amount"] += job_amount

    # Round total amounts
    for v in landscaper_dict.values():
        v["total_amount"] = round(v["total_amount"], 2)

    return Response(list(landscaper_dict.values()), status=200)


# recent payments user

class RecentPaymentsAPIView(APIView):
    """
    Returns recent PAID payments for the authenticated user.
    
    - Client: sees their own payments
    - Landscaper: sees payments from their clients
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get("limit", 10)) 

        queryset = ServiceSchedule.objects.filter(
            payment_status=PaymentStatus.PAID
        )

        # ------------------------------
        # Role-based filtering
        # ------------------------------
        if hasattr(user, "clientprofile"):
            queryset = queryset.filter(client=user.clientprofile)

        elif hasattr(user, "landscaperprofilies"):
            queryset = queryset.filter(landscaper=user.landscaperprofilies)

        else:
            return Response({"detail": "Invalid user role"}, status=400)

        # ------------------------------
        # Ordering: most recent first
        # ------------------------------
        queryset = queryset.order_by("-scheduled_date", "-scheduled_time")[:limit]

        # ------------------------------
        # Serialize payments
        # ------------------------------
        payments_data = []
        for schedule in queryset:
            client_profile = getattr(schedule.client, "user", None)
            profile_image = None
            if client_profile:
                cp = getattr(schedule.client, "image", None)
                profile_image = cp.url if cp else None

            # Use existing serializer data
            serialized = PaymentHistorySerializer(schedule, context={"request": request}).data

            # Add client profile image
            serialized["client_profile_image"] = profile_image

            payments_data.append(serialized)

        return Response({
            "count": queryset.count(),
            "results": payments_data
        })

# for admin
# Admin: Stripe Overview by Day
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_daily_income_overview(request):
    """
    Admin: Daily income overview (USD)
    Includes:
    - Client job payments (service price + 2% fee)
    - Landscaper subscription payments
    """

    days = int(request.GET.get("days", 30))
    start_date = datetime.now() - timedelta(days=days)

  
    # Job income (clients)
    # ============================
    job_income = (
        ServiceSchedule.objects.filter(
            payment_status=PaymentStatus.PAID,
            scheduled_date__gte=start_date
        )
        .annotate(day=TruncDate("scheduled_date"))
        .values("day")
        .annotate(
            income=Sum(
                F("service__price") * 1.02,
                output_field=FloatField()
            )
        )
    )

    job_map = {row["day"]: row["income"] or 0.0 for row in job_income}


    # Subscription income (landscapers)
    # ============================
    subscription_income = (
        Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            created_at__gte=start_date
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            income=Sum(F("plan__price"), output_field=FloatField())
        )
    )

    sub_map = {row["day"]: row["income"] or 0.0 for row in subscription_income}


    # Merge daily income
    # ============================
    all_days = sorted(set(job_map.keys()) | set(sub_map.keys()))

    daily_income = [
        {
            "day": day,
            "income": round(job_map.get(day, 0.0) + sub_map.get(day, 0.0), 2)
        }
        for day in all_days
    ]

    return Response({
        "currency": "USD",
        "daily_income": daily_income
    })




@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_income_overview(request):
    """
    Admin: Income overview
    Query param: ?period=daily|weekly|monthly|yearly
    """
    period = request.GET.get("period", "daily").lower()
    today = datetime.now().date()

    if period == "daily":
        start_date = today - timedelta(days=30)
        trunc = TruncDate
        label = "day"
    elif period == "weekly":
        start_date = today - timedelta(weeks=12)
        trunc = TruncWeek
        label = "week_start"
    elif period == "monthly":
        start_date = today.replace(day=1) - timedelta(days=365)
        trunc = TruncMonth
        label = "month"
    elif period == "yearly":
        start_date = today.replace(month=1, day=1) - timedelta(days=365*12)
        trunc = TruncYear
        label = "year"
    else:
        return Response({"detail": "Invalid period. Use daily, weekly, monthly, yearly."}, status=400)

    # -----------------------------
    # Job income
    # -----------------------------
    jobs = (
        ServiceSchedule.objects.filter(payment_status=PaymentStatus.PAID, scheduled_date__gte=start_date)
        .annotate(period=trunc("scheduled_date"))
        .values("period")
        .annotate(income=Sum(F("service__price") * 1.02, output_field=FloatField()))
    )

    # -----------------------------
    # Subscription income
    # -----------------------------
    subs = (
        Subscription.objects.filter(status=SubscriptionStatus.ACTIVE, created_at__date__gte=start_date)
        .annotate(period=trunc("created_at"))
        .values("period")
        .annotate(income=Sum(F("plan__price"), output_field=FloatField()))
    )

    # -----------------------------
    # Merge incomes
    # -----------------------------
    income_map = {}
    for row in jobs:
        p = row["period"]
        if isinstance(p, datetime):
            p = p.date()
        income_map[p] = row["income"] or 0.0

    for row in subs:
        p = row["period"]
        if isinstance(p, datetime):
            p = p.date()
        income_map[p] = income_map.get(p, 0.0) + (row["income"] or 0.0)

    # -----------------------------
    # Prepare response
    # -----------------------------
    overview = [
        {label: k.strftime("%Y-%m-%d") if label != "year" else k.year, "income": round(v, 2)}
        for k, v in sorted(income_map.items())
    ]

    return Response({"currency": "USD", "period": period, "overview": overview})


# Admin: Total Transactions Summary
# ============================

@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_transaction_summary(request):
    """
    Admin financial summary:
    - Total transactions (jobs + subscriptions)
    - Total platform fees (2% from job payments only)
    """

    # Client Job Payments
    # ======================
    paid_jobs = ServiceSchedule.objects.filter(
        payment_status=PaymentStatus.PAID
    )

    total_job_amount = paid_jobs.aggregate(
        total=Sum('service__price', output_field=FloatField())
    )['total'] or 0.0

    job_platform_fee = round(total_job_amount * 0.02, 2)
    job_total_transactions = round(total_job_amount + job_platform_fee, 2)


    # Subscription Payments
    # ======================
    active_subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE
    )

    total_subscription_amount = active_subscriptions.aggregate(
        total=Sum('plan__price', output_field=FloatField())
    )['total'] or 0.0


    # Grand Totals
    # ======================
    total_transactions = round(
        job_total_transactions + total_subscription_amount,
        2
    )

    total_platform_fees = round(job_platform_fee, 2)

    return Response({
        "transactions": {
            "job_transactions": job_total_transactions,
            "subscription_transactions": total_subscription_amount,
            "total_transactions": total_transactions
        },
        "platform_fees": {
            "job_platform_fee_2_percent": total_platform_fees
        }
    })



# Admin: Payment Details
from rest_framework.pagination import PageNumberPagination


# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def stripe_all_payments(request):
#     """
#     Admin: All Stripe payments with user/job IDs for reference.
#     """

#     data = []

#     # =========================
#     # Client Job Payments
#     # =========================
#     paid_jobs = (
#         ServiceSchedule.objects
#         .filter(payment_status=PaymentStatus.PAID)
#         .select_related("client__user", "service")
#     )

#     for job in paid_jobs:
#         service_price = float(job.service.price)
#         platform_fee = round(service_price * 0.02, 2)

#         data.append({
#             "id": job.id,                   # job ID
#             "user_id": job.client.user.id,  # client user ID
#             "role": "client",
#             "name": job.client.user.name,
#             "email": job.client.user.email,
#             "amount_paid": round(service_price + platform_fee, 2),
#             "platform_fee": platform_fee,
#             "transaction_id": job.stripe_payment_id,
#             "date": job.scheduled_date,
#             "source": "job_payment"
#         })

#     # =========================
#     # Landscaper Subscription Payments
#     # =========================
#     subscriptions = (
#         Subscription.objects
#         .filter(stripe_subscription_id__isnull=False)
#         .select_related("user", "plan")
#     )

#     for sub in subscriptions:
#         data.append({
#             "id": sub.id,              # subscription ID
#             "user_id": sub.user.id,    # landscaper user ID
#             "role": "landscaper",
#             "name": sub.user.name,
#             "email": sub.user.email,
#             "amount_paid": float(sub.plan.price),
#             "platform_fee": 0.0,
#             "transaction_id": sub.stripe_subscription_id,
#             "date": sub.created_at,
#             "source": "subscription"
#         })

#     # =========================
#     # PAGINATION
#     # =========================
#     paginator = PageNumberPagination()
#     paginator.page_size = 10

#     result_page = paginator.paginate_queryset(data, request)
#     return paginator.get_paginated_response(result_page)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def stripe_all_payments(request):
    """
    Admin: All Stripe payments with user/job IDs.
    Supports:
    - pagination
    - CSV download (?download=csv)
    """

    data = []

    # =========================
    # Client Job Payments
    # =========================
    paid_jobs = (
        ServiceSchedule.objects
        .filter(payment_status=PaymentStatus.PAID)
        .select_related("client__user", "service")
    )

    for job in paid_jobs:
        service_price = float(job.service.price)
        platform_fee = round(service_price * 0.02, 2)

        data.append({
            "record_id": job.id,
            "user_id": job.client.user.id,
            "role": "client",
            "type": "job_payment",
            "name": job.client.user.name,
            "email": job.client.user.email,
            "amount_paid": round(service_price + platform_fee, 2),
            "platform_fee": platform_fee,
            "transaction_id": job.stripe_payment_id,
            "date": job.scheduled_date
        })

    # =========================
    # Landscaper Subscription Payments
    # =========================
    subscriptions = (
        Subscription.objects
        .filter(stripe_subscription_id__isnull=False)
        .select_related("user", "plan")
    )

    for sub in subscriptions:
        data.append({
            "record_id": sub.id,
            "user_id": sub.user.id,
            "role": "landscaper",
            "type": "subscription",
            "name": sub.user.name,
            "email": sub.user.email,
            "amount_paid": float(sub.plan.price),
            "platform_fee": 0.0,
            "transaction_id": sub.stripe_subscription_id,
            "date": sub.created_at
        })

    # =========================
    # CSV DOWNLOAD
    # =========================
    if request.GET.get("download") == "csv":

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="stripe_payments_report.csv"'

        writer = csv.writer(response)

        writer.writerow([
            "Record ID",
            "User ID",
            "Role",
            "Type",
            "Name",
            "Email",
            "Amount Paid",
            "Platform Fee",
            "Transaction ID",
            "Date"
        ])

        for item in data:
            writer.writerow([
                item["record_id"],
                item["user_id"],
                item["role"],
                item["type"],
                item["name"],
                item["email"],
                item["amount_paid"],
                item["platform_fee"],
                item["transaction_id"],
                item["date"]
            ])

        return response

    # =========================
    # PAGINATION
    # =========================
    paginator = PageNumberPagination()
    paginator.page_size = 10

    result_page = paginator.paginate_queryset(data, request)
    return paginator.get_paginated_response(result_page)
# delete views

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
@transaction.atomic
def delete_user_financial_data(request, user_id):
    """
    Admin: Delete all financial records of a particular user
    - Deletes PAID job payments
    - Deletes subscriptions
    """

    user = get_object_or_404(User, id=user_id)

    if request.user.id == user.id:
        return Response(
            {"error": "You cannot delete your own financial data."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Delete Paid Job Payments (Client or Landscaper side)
    job_qs = ServiceSchedule.objects.filter(
        Q(client__user=user) | Q(landscaper__user=user),
        payment_status=PaymentStatus.PAID
    )

    deleted_jobs_count = job_qs.count()
    job_qs.delete()

    # Delete Subscriptions
    sub_qs = Subscription.objects.filter(user=user)

    deleted_sub_count = sub_qs.count()
    sub_qs.delete()

    return Response(
        {
            "message": "User financial data deleted successfully",
            "user_id": user.id,
            "deleted_job_payments": deleted_jobs_count,
            "deleted_subscriptions": deleted_sub_count,
        },
        status=status.HTTP_200_OK
    )


# revenue overviw for pro landscapers
class ProLandscaperMonthlyRevenueView(APIView):
    permission_classes = [IsLandscaper]

    def get(self, request):
        user = request.user
        landscaper = getattr(user, "landscaperprofilies", None)
        if not landscaper:
            return Response({"error": "No landscaper profile found"}, status=404)

        jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper,
            is_completed=True
        )

        current_year = datetime.now().year

        # Monthly revenue (paid jobs)
        monthly_revenue_qs = (
            jobs.filter(payment_status=PaymentStatus.PAID)
            .annotate(month=TruncMonth("scheduled_date"))
            .values("month")
            .annotate(
                total_amount=Sum(
                    F("service__price") * Value(1.02, output_field=FloatField()),
                    output_field=FloatField()
                )
            )
            .order_by("month")
        )

        # Initialize all months with 0
        monthly_revenue = OrderedDict()
        for month in range(1, 13):
            monthly_revenue[f"{current_year}-{month:02d}"] = 0.0

        # Fill months that have revenue
        for item in monthly_revenue_qs:
            month_str = item["month"].strftime("%Y-%m")
            monthly_revenue[month_str] = round(item["total_amount"], 2) if item["total_amount"] else 0.0

        # Yearly revenue
        yearly_revenue = jobs.filter(
            payment_status=PaymentStatus.PAID,
            scheduled_date__year=current_year
        ).aggregate(
            total=Sum(F("service__price") * Value(1.02, output_field=FloatField()), output_field=FloatField())
        )["total"] or 0

        # Total revenue
        total_revenue = jobs.filter(payment_status=PaymentStatus.PAID).aggregate(
            total=Sum(F("service__price") * Value(1.02, output_field=FloatField()), output_field=FloatField())
        )["total"] or 0

        # Pending payments
        pending_amount = jobs.filter(payment_status=PaymentStatus.PENDING).aggregate(
            total=Sum(F("service__price") * Value(1.02, output_field=FloatField()), output_field=FloatField())
        )["total"] or 0

        data = {
            "monthly_revenue": [
                {"month": month, "total_amount": total}
                for month, total in monthly_revenue.items()
            ],
            "yearly_revenue": round(yearly_revenue, 2),
            "total_revenue": round(total_revenue, 2),
            "pending_amount": round(pending_amount, 2)
        }

        return Response(data, status=200)




# stripe vs cash
class AdminStripeVsCashDashboardAPIView(APIView):
    """
    Admin: Dashboard showing total payments by type:
    - Stripe
    - Cash
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        # --------------------------
        # Stripe payments
        # --------------------------
        stripe_payments = ServiceSchedule.objects.filter(
            payment_status=PaymentStatus.PAID
        ).exclude(stripe_payment_id__isnull=True).exclude(stripe_payment_id__exact='')

        stripe_total = stripe_payments.aggregate(
            total=Sum(F("service__price"), output_field=FloatField())
        )["total"] or 0.0

        # --------------------------
        # Cash payments
        # --------------------------
        cash_payments = ServiceSchedule.objects.filter(
            payment_status=PaymentStatus.PAID,
            stripe_payment_id__isnull=True
        )

        cash_total = cash_payments.aggregate(
            total=Sum(F("service__price"), output_field=FloatField())
        )["total"] or 0.0

        # --------------------------
        # Total payments & ratio
        # --------------------------
        total = stripe_total + cash_total
        stripe_percentage = round((stripe_total / total) * 100, 2) if total else 0
        cash_percentage = round((cash_total / total) * 100, 2) if total else 0

        return Response({
            "total_payments": round(total, 2),
            "stripe": {
                "amount": round(stripe_total, 2),
                "percentage": stripe_percentage
            },
            "cash": {
                "amount": round(cash_total, 2),
                "percentage": cash_percentage
            }
        })