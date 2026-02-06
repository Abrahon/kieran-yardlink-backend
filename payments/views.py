
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
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


# payments views
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_checkout_session(request):
    """
    Client pays for a completed job (ServiceSchedule)
    schedule_id is passed in the POST body.
    """
    from .enums import PaymentStatus
    import stripe

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
        return Response({"error": "Job is not yet completed."}, status=400)

    if schedule.payment_status == PaymentStatus.PAID:
        return Response({"error": "Job already paid"}, status=400)

    amount = int(schedule.service.price * 100)  # cents
    platform_fee = int(amount * 0.02)           # 2% platform fee
    total_amount = amount + platform_fee        # client pays extra 2%

    landscaper = schedule.landscaper
    if not landscaper:
        return Response({"error": "No landscaper assigned to this job"}, status=400)

    #  Ensure Stripe Standard account exists for landscaper
    if not landscaper.stripe_account_id:
        account = stripe.Account.create(
            type="standard",      # Use standard for Bangladesh
            country="BD",
            email=landscaper.user.email
        )
        landscaper.stripe_account_id = account.id
        landscaper.save()

    # Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": total_amount,
                "product_data": {
                    "name": f"{schedule.service.name} (Job ID {schedule.id})",
                },
            },
            "quantity": 1,
        }],


        # transfer_data not allowed for Standard accounts in BD
        success_url=f"http://localhost:8000/api/success/?schedule_id={schedule.id}",
        cancel_url=f"http://localhost:8000/api/cancel/?schedule_id={schedule.id}",
        metadata={
            "schedule_id": str(schedule.id),
            "platform_fee": str(platform_fee)
        }
    )

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



# Cash Payment
class CashPaymentScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id):
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id, client=request.user.clientprofile)

        if not schedule.is_completed:
            return Response({"error": "Job not completed yet"}, status=400)

        if schedule.payment_status == PaymentStatus.PAID:
            return Response({"error": "Already paid"}, status=400)

        schedule.payment_status = PaymentStatus.CASH_PENDING
        schedule.save(update_fields=["payment_status"])
        return Response({"message": "Cash payment selected", "payment_status": schedule.payment_status})


# Stripe Webhook for auto-payment
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except Exception:
        return HttpResponse(status=400)

    # Only handle successful checkout sessions
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Check if the payment is actually successful
        if session.get("payment_status") != "paid":
            return HttpResponse(status=200)

        schedule_id = session.get("metadata", {}).get("schedule_id")
        if schedule_id:
            try:
                schedule = ServiceSchedule.objects.get(id=schedule_id)
                schedule.payment_status = PaymentStatus.PAID
                schedule.stripe_payment_id = session.get("id")  # store session ID
                schedule.save(update_fields=["payment_status", "stripe_payment_id"])
            except ServiceSchedule.DoesNotExist:
                return HttpResponse(status=400)

    return HttpResponse(status=200)


# payment history
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def landscaper_payment_history(request):
    """
    Returns landscaper payment history with monthly/yearly summary.
    Shows all jobs completed by landscaper.
    Payment can be pending or paid.
    """
    user = request.user

    try:
        landscaper = user.landscaperprofilies  # your existing model
    except LandscaperProfilies.DoesNotExist:
        return Response({"error": "No landscaper profile found"}, status=404)

    # All jobs completed by landscaper
    schedules = ServiceSchedule.objects.filter(
        landscaper=landscaper,
        is_completed=True  # only show jobs completed by landscaper
    ).select_related('client', 'service').order_by('-scheduled_date')

    serializer = PaymentHistorySerializer(schedules, many=True)

    current_month = datetime.now().month
    current_year = datetime.now().year

    # Monthly summary
    monthly_jobs = schedules.filter(
        scheduled_date__year=current_year,
        scheduled_date__month=current_month
    )
    monthly_total_completed_jobs = monthly_jobs.count()
    monthly_pending_jobs = monthly_jobs.filter(payment_status='pending').count()

    # Yearly summary
    yearly_jobs = schedules.filter(scheduled_date__year=current_year)
    yearly_total_completed_jobs = yearly_jobs.count()
    yearly_pending_jobs = yearly_jobs.filter(payment_status='pending').count()

    return Response({
        "payment_history": serializer.data,
        "summary": {
            "monthly_total_completed_jobs": monthly_total_completed_jobs,
            "monthly_pending_jobs": monthly_pending_jobs,
            "yearly_total_completed_jobs": yearly_total_completed_jobs,
            "yearly_pending_jobs": yearly_pending_jobs,
        }
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
@api_view(["GET"])
@permission_classes([IsAdminUser])
def stripe_all_payments(request):
    """
    Admin: All Stripe payments
    - Client job payments (with 2% platform fee)
    - Landscaper subscription payments (NO platform fee)
    """

    data = []

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
            "role": "client",
            "name": job.client.user.name,
            "email": job.client.user.email,
            "amount_paid": round(service_price + platform_fee, 2),
            "platform_fee": platform_fee,
            "transaction_id": job.stripe_payment_id,
            "date": job.scheduled_date,
            "source": "job_payment"
        })


    # Landscaper Subscription Payments
    # =========================
    subscriptions = (
        Subscription.objects
        .filter(stripe_subscription_id__isnull=False)
        .select_related("user", "plan")
    )

    for sub in subscriptions:
        data.append({
            "role": "landscaper",
            "name": sub.user.name,
            "email": sub.user.email,
            "amount_paid": float(sub.plan.price),
            "platform_fee": 0.0,  #  No 2% fee for subscriptions
            "transaction_id": sub.stripe_subscription_id,
            "date": sub.created_at,
            "source": "subscription"
        })

    return Response({
        "total_records": len(data),
        "payments": data
    })

