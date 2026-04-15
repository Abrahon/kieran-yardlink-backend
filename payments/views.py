
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, F, FloatField
from .serializers import PaymentHistorySerializer
from datetime import datetime
from profiles.models import LandscaperProfilies

from datetime import datetime, timedelta
from django.db.models.functions import TruncDate
from rest_framework.permissions import IsAdminUser
from subscriptions.models import Subscription
from subscriptions.enums import SubscriptionStatus
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.shortcuts import get_object_or_404
from common.permissions import IsClient,IsLandscaper
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils.timezone import now
from profiles.models import LandscaperProfilies
from payments.serializers import PaymentHistorySerializer
from django.db.models import Sum, F
from rest_framework.response import Response
from profiles.models import LandscaperProfilies
from django.db.models import F, FloatField, Value, Sum
from django.db.models.functions import Coalesce, Cast
from django.utils.timezone import now
from profiles.models import LandscaperProfilies
from rest_framework.views import APIView
from profiles.models import ClientProfile
from datetime import datetime, timedelta
from django.db.models import Sum, FloatField, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.mail import send_mail
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
from datetime import datetime
from collections import OrderedDict
from calendar import monthrange
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from invoice.models import Invoice
from payments.serializers import PaymentHistorySerializer
from invoice.models import Invoice
from jobs.models import Job
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .enums import PaymentStatus

from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils.timezone import now

from rest_framework.decorators import api_view, permission_classes

from rest_framework.response import Response

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()
from collections import OrderedDict
from datetime import datetime

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response

from jobs.models import Job
from common.permissions import IsLandscaper
from invoice.models import Invoice
from jobs.models import Job
import csv
from datetime import datetime, time
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination






# payment notification
from notifications.services import send_push_notification

def payment_success(request):
    payment = Payment.objects.create(...)

    send_push_notification(
        user=payment.user,
        title="Payment Received",
        message="Your payment has been completed",
        notification_type="payment",
        data={"screen": "payment_history"}
    )

    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_invoice_checkout_session(request):
    invoice_id = request.data.get("invoice_id")
    if not invoice_id:
        return Response({"error": "invoice_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    client = getattr(request.user, "clientprofile", None)
    if not client:
        return Response({"error": "Client profile not found"}, status=status.HTTP_403_FORBIDDEN)

    try:
        invoice = Invoice.objects.select_related("job", "job__client", "job__landscaper").get(
            id=invoice_id,
            job__client=client
        )
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

    if invoice.status == Invoice.Status.PAID:
        return Response({"message": "Invoice already paid"}, status=status.HTTP_200_OK)

    try:
        session = create_invoice_checkout_session(invoice)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    invoice.status = Invoice.Status.PENDING
    invoice.stripe_session_id = session.id
    invoice.stripe_checkout_url = session.url
    invoice.save(update_fields=["status", "stripe_session_id", "stripe_checkout_url", "updated_at"])

    return Response({
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "checkout_url": session.url,
    }, status=status.HTTP_200_OK)
    


# Success / Cancel Endpoints
@api_view(["GET"])
def payment_success(request):
    invoice_id = request.GET.get("invoice_id")
    session_id = request.GET.get("session_id")
    return Response({
        "message": "Payment successful",
        "invoice_id": invoice_id,
        "session_id": session_id,
    })


@api_view(["GET"])
def payment_cancel(request):
    invoice_id = request.GET.get("invoice_id")
    return Response({
        "message": "Payment cancelled",
        "invoice_id": invoice_id,
    })




class CashPaymentScheduleAPIView(APIView):
    """
    Client selects cash payment for a completed job.
    Sends email to landscaper.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id):
        # 1️⃣ Get the schedule for this client
        client_profile = getattr(request.user, "clientprofile", None)
        schedule = get_object_or_404(Job, id=schedule_id, client=client_profile)

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
        schedule = get_object_or_404(Job, id=schedule_id, landscaper=landscaper_profile)

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



# optional QuickBooks imports

@csrf_exempt
def payment_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_PAYMENT_WEBHOOK_SECRET

    if not sig_header:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type in ["checkout.session.completed", "checkout.session.async_payment_succeeded"]:
        invoice_id = data_object.get("metadata", {}).get("invoice_id")
        stripe_session_id = data_object.get("id")

        if invoice_id:
            try:
                invoice = Invoice.objects.select_related(
                    "job",
                    "job__landscaper",
                    "job__client",
                    "job__client__user",
                    "job__external_client",
                ).get(id=invoice_id)

                # avoid duplicate updates
                if invoice.status != Invoice.Status.PAID:
                    invoice.status = Invoice.Status.PAID
                    invoice.paid_at = timezone.now()
                    invoice.stripe_session_id = stripe_session_id
                    invoice.save(update_fields=["status", "paid_at", "stripe_session_id", "updated_at"])

                    if invoice.job:
                        invoice.job.payment_status = Job.PaymentStatus.PAID
                        invoice.job.save(update_fields=["payment_status", "updated_at"])

                # OPTIONAL: auto sync paid invoice to QuickBooks
                try:
                    connection = QuickBooksConnection.objects.get(
                        landscaper=invoice.job.landscaper,
                        is_active=True
                    )

                    # store these in DB/config later instead of hardcoding
                    service_item_id = getattr(settings, "QUICKBOOKS_DEFAULT_SERVICE_ITEM_ID", None)
                    deposit_to_account_id = getattr(settings, "QUICKBOOKS_DEFAULT_DEPOSIT_ACCOUNT_ID", None)

                    if service_item_id:
                        customer = upsert_customer(connection, invoice)
                        qbo_invoice = qbo_create_invoice(connection, invoice, customer["Id"], service_item_id)

                        if deposit_to_account_id:
                            qbo_create_payment(
                                connection,
                                invoice,
                                customer["Id"],
                                qbo_invoice["Id"],
                                deposit_to_account_id,
                            )

                except QuickBooksConnection.DoesNotExist:
                    pass
                except Exception as e:
                    # do not fail Stripe webhook because of QuickBooks sync
                    print("QuickBooks auto-sync failed:", str(e))

            except Invoice.DoesNotExist:
                pass

    return HttpResponse(status=200)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def landscaper_payment_history(request):
    """
    Landscaper view:
    - payment history for all completed jobs/invoices
    - revenue summary:
        - monthly_paid / monthly_pending
        - yearly_paid / yearly_pending
        - total_paid / total_pending
    """
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "No landscaper profile found"}, status=404)

    invoices = Invoice.objects.filter(
        job__landscaper=landscaper,
        job__status="completed"
    ).select_related(
        "job",
        "job__client",
        "job__client__user",
        "job__landscaper",
        "job__landscaper__user",
        "job__job_property",
    ).prefetch_related(
        "job__items"
    ).order_by("-job__completed_at", "-created_at")

    serializer = PaymentHistorySerializer(invoices, many=True)

    today = now()
    current_month = today.month
    current_year = today.year

    monthly_invoices = invoices.filter(
        created_at__year=current_year,
        created_at__month=current_month
    )
    yearly_invoices = invoices.filter(created_at__year=current_year)

    money_field = DecimalField(max_digits=12, decimal_places=2)

    monthly_paid = monthly_invoices.filter(status="paid").aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    monthly_pending = monthly_invoices.filter(status__in=["pending", "sent"]).aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    yearly_paid = yearly_invoices.filter(status="paid").aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    yearly_pending = yearly_invoices.filter(status__in=["pending", "sent"]).aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    total_paid = invoices.filter(status="paid").aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    total_pending = invoices.filter(status__in=["pending", "sent"]).aggregate(
        total=Coalesce(
            Sum("total"),
            Value(0),
            output_field=money_field
        )
    )["total"]

    return Response({
        "payment_history": serializer.data,
        "revenue_summary": {
            "monthly_paid": round(float(monthly_paid or 0), 2),
            "monthly_pending": round(float(monthly_pending or 0), 2),
            "yearly_paid": round(float(yearly_paid or 0), 2),
            "yearly_pending": round(float(yearly_pending or 0), 2),
            "total_paid": round(float(total_paid or 0), 2),
            "total_pending": round(float(total_pending or 0), 2),
        }
    }, status=200)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def client_payment_history(request):
    """
    Client view:
    - shows all landscapers the client worked with
    - each landscaper includes:
        - name, email
        - completed jobs/invoices
        - property/location
        - completed date
        - total jobs worked
        - total amount invoiced
        - pay_url if still pending
    """
    client = getattr(request.user, "clientprofile", None)
    if not client:
        return Response({"error": "Client profile not found"}, status=404)

    invoices = Invoice.objects.filter(
        job__client=client,
        job__status="completed"
    ).select_related(
        "job",
        "job__client",
        "job__client__user",
        "job__landscaper",
        "job__landscaper__user",
        "job__job_property",
    ).prefetch_related(
        "job__items"
    ).order_by("-job__completed_at", "-created_at")

    landscaper_dict = {}

    for invoice in invoices:
        landscaper = invoice.job.landscaper
        landscaper_id = landscaper.id

        personal = getattr(landscaper.user, "landscaperprofilies", None)
        landscaper_name = personal.name if personal and personal.name else landscaper.business_name
        landscaper_email = landscaper.user.email if landscaper.user else ""

        if landscaper_id not in landscaper_dict:
            landscaper_dict[landscaper_id] = {
                "landscaper_id": landscaper_id,
                "landscaper_name": landscaper_name,
                "landscaper_email": landscaper_email,
                "jobs_count": 0,
                "total_amount": 0.0,
                "jobs": []
            }

        invoice_amount = float(invoice.total or 0)

        landscaper_dict[landscaper_id]["jobs"].append({
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "job_id": invoice.job.id,
            "property_address": str(invoice.job.job_property) if invoice.job.job_property else "",
            "completed_at": invoice.job.completed_at.strftime("%Y-%m-%d %H:%M:%S") if invoice.job.completed_at else None,
            "payment_status": invoice.status,
            "amount": round(invoice_amount, 2),
            "pay_url": invoice.stripe_checkout_url,
            "completed_items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "item_type": item.item_type,
                    "price": round(float(item.price or 0), 2)
                }
                for item in invoice.job.items.filter(is_completed=True).order_by("sort_order", "id")
            ]
        })

        landscaper_dict[landscaper_id]["jobs_count"] += 1
        landscaper_dict[landscaper_id]["total_amount"] += invoice_amount

    for value in landscaper_dict.values():
        value["total_amount"] = round(value["total_amount"], 2)

    return Response(list(landscaper_dict.values()), status=200)



# recent payments user

class RecentPaymentsAPIView(APIView):
    """
    Returns recent payments for the authenticated user.

    - Client: sees their own invoice payments
    - Landscaper: sees invoice payments from their jobs
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get("limit", 10))

        queryset = (
            Invoice.objects
            .select_related(
                "job",
                "job__client__user",
                "job__external_client",
                "job__landscaper__user",
                "job__job_property",
                "job__booking",
            )
            .prefetch_related("job__items")
            .exclude(stripe_session_id__isnull=True)
            .exclude(stripe_session_id="")
        )

        # ------------------------------
        # Role-based filtering
        # ------------------------------
        if hasattr(user, "clientprofile"):
            queryset = queryset.filter(job__client=user.clientprofile)

        elif hasattr(user, "landscaper_profile"):
            queryset = queryset.filter(job__landscaper=user.landscaper_profile)

        else:
            return Response(
                {"detail": "Invalid user role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ------------------------------
        # Ordering: most recent first
        # ------------------------------
        queryset = queryset.order_by("-created_at")[:limit]

        # ------------------------------
        # Serialize payments
        # ------------------------------
        payments_data = []
        for invoice in queryset:
            client_profile_image = None

            job = getattr(invoice, "job", None)
            client = getattr(job, "client", None)

            if client:
                image = getattr(client, "image", None)
                if image:
                    try:
                        client_profile_image = image.url
                    except Exception:
                        client_profile_image = None

            serialized = PaymentHistorySerializer(
                invoice,
                context={"request": request}
            ).data

            serialized["client_profile_image"] = client_profile_image
            payments_data.append(serialized)

        return Response({
            "count": len(payments_data),
            "results": payments_data
        }, status=status.HTTP_200_OK)



# Admin: Total Transactions Summary
# ============================

# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def admin_transaction_stats(request):
#     """
#     Admin financial summary:
#     - Total transactions (jobs + subscriptions)
#     - Total platform fees (2% from job payments only)
#     """

#     # Client Job Payments
#     # ======================
#     paid_jobs = Job.objects.filter(
#         payment_status=PaymentStatus.PAID
#     )

#     total_job_amount = paid_jobs.aggregate(
#         total=Sum('service__price', output_field=FloatField())
#     )['total'] or 0.0

#     job_platform_fee = round(total_job_amount * 0.02, 2)
#     job_total_transactions = round(total_job_amount + job_platform_fee, 2)


#     # Subscription Payments
#     # ======================
#     active_subscriptions = Subscription.objects.filter(
#         status=SubscriptionStatus.ACTIVE
#     )

#     total_subscription_amount = active_subscriptions.aggregate(
#         total=Sum('plan__price', output_field=FloatField())
#     )['total'] or 0.0


#     # Grand Totals
#     # ======================
#     total_transactions = round(
#         job_total_transactions + total_subscription_amount,
#         2
#     )

#     total_platform_fees = round(job_platform_fee, 2)

#     return Response({
#         "transactions": {
#             "job_transactions": job_total_transactions,
#             "subscription_transactions": total_subscription_amount,
#             "total_transactions": total_transactions
#         },
#         "platform_fees": {
#             "job_platform_fee_2_percent": total_platform_fees
#         }
#     })


# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def admin_transaction_stats(request):
#     """
#     Admin financial summary:
#     - Total service transactions
#     - Total subscription transactions
#     - Total transaction revenue
#     - Total platform fees (from invoices only)
#     """

#     # ======================
#     # Service / Invoice Payments
#     # ======================
#     invoices = (
#         Invoice.objects
#         .exclude(stripe_session_id__isnull=True)
#         .exclude(stripe_session_id="")
#     )

#     total_service_amount = invoices.aggregate(
#         total=Coalesce(
#             Sum("total"),
#             Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
#         )
#     )["total"] or Decimal("0.00")

#     total_platform_fees = invoices.aggregate(
#         total=Coalesce(
#             Sum("service_fee_amount"),
#             Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
#         )
#     )["total"] or Decimal("0.00")

#     service_transactions_count = invoices.count()

#     # ======================
#     # Subscription Payments
#     # ======================
#     subscriptions = (
#         Subscription.objects
#         .exclude(stripe_subscription_id__isnull=True)
#         .exclude(stripe_subscription_id="")
#         .select_related("plan")
#     )

#     total_subscription_amount = Decimal("0.00")
#     for sub in subscriptions:
#         plan_price = Decimal(str(sub.plan.price or 0))
#         if hasattr(sub, "discount_override") and sub.discount_override:
#             plan_price -= plan_price * Decimal(str(sub.discount_override)) / Decimal("100")
#         total_subscription_amount += plan_price

#     subscription_transactions_count = subscriptions.count()

#     # ======================
#     # Grand Totals
#     # ======================
#     total_transaction_revenue = total_service_amount + total_subscription_amount
#     total_transactions_count = service_transactions_count + subscription_transactions_count

#     return Response({
#         "status": "success",
#         "data": {
#             "transactions": {
#                 "service_transactions_amount": round(float(total_service_amount), 2),
#                 "subscription_transactions_amount": round(float(total_subscription_amount), 2),
#                 "total_transaction_revenue": round(float(total_transaction_revenue), 2),
#                 "service_transactions_count": service_transactions_count,
#                 "subscription_transactions_count": subscription_transactions_count,
#                 "total_transactions_count": total_transactions_count
#             },
#             "platform_fees": {
#                 "service_platform_fee_total": round(float(total_platform_fees), 2)
#             }
#         }
#     }, status=status.HTTP_200_OK)
    

# Admin: Payment Details
def parse_date_range(start_str=None, end_str=None):
    start_dt = None
    end_dt = None

    try:
        if start_str:
            start_dt = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(start_str, "%Y-%m-%d").date(),
                    time.min
                )
            )

        if end_str:
            end_dt = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(end_str, "%Y-%m-%d").date(),
                    time.max
                )
            )
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("start_date cannot be greater than end_date.")

    return start_dt, end_dt




from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from invoice.models import Invoice
from subscriptions.models import Subscription


def get_month_range(dt):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)

    return start, next_month


def percent_change(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_dashboard_stats(request):
    now = timezone.now()

    # Current month
    current_start, current_end = get_month_range(now)

    # Last month
    last_anchor = current_start - timedelta(days=1)
    last_start, last_end = get_month_range(last_anchor)

    # Previous month
    prev_anchor = last_start - timedelta(days=1)
    prev_start, prev_end = get_month_range(prev_anchor)

    # =========================
    # SERVICE (INVOICE)
    # =========================
    def get_invoice_data(start, end):
        qs = (
            Invoice.objects
            .filter(
                created_at__gte=start,
                created_at__lt=end,
            )
            .exclude(stripe_session_id__isnull=True)
            .exclude(stripe_session_id="")
        )

        total = qs.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        fee = qs.aggregate(total=Sum("service_fee_amount"))["total"] or Decimal("0.00")
        count = qs.count()

        return total, fee, count

    # =========================
    # SUBSCRIPTIONS
    # =========================
    def get_subscription_data(start, end):
        qs = (
            Subscription.objects
            .filter(
                created_at__gte=start,
                created_at__lt=end,
            )
            .exclude(stripe_subscription_id__isnull=True)
            .exclude(stripe_subscription_id="")
            .select_related("plan")
        )

        total = Decimal("0.00")

        for sub in qs:
            price = Decimal(str(sub.plan.price or 0))
            if hasattr(sub, "discount_override") and sub.discount_override:
                price -= price * Decimal(str(sub.discount_override)) / Decimal("100")
            total += price

        count = qs.count()

        return total, count

    # =========================
    # CURRENT MONTH
    # =========================
    cur_invoice_total, cur_fee, cur_invoice_count = get_invoice_data(current_start, current_end)
    cur_sub_total, cur_sub_count = get_subscription_data(current_start, current_end)

    cur_total_revenue = cur_invoice_total + cur_sub_total
    cur_total_transactions = cur_invoice_count + cur_sub_count

    # =========================
    # LAST MONTH
    # =========================
    last_invoice_total, last_fee, last_invoice_count = get_invoice_data(last_start, last_end)
    last_sub_total, last_sub_count = get_subscription_data(last_start, last_end)

    last_total_revenue = last_invoice_total + last_sub_total
    last_total_transactions = last_invoice_count + last_sub_count

    # =========================
    # PREVIOUS MONTH
    # =========================
    prev_invoice_total, prev_fee, prev_invoice_count = get_invoice_data(prev_start, prev_end)
    prev_sub_total, prev_sub_count = get_subscription_data(prev_start, prev_end)

    prev_total_revenue = prev_invoice_total + prev_sub_total
    prev_total_transactions = prev_invoice_count + prev_sub_count

    # =========================
    # CALCULATE %
    # =========================
    revenue_change = percent_change(last_total_revenue, prev_total_revenue)
    fee_change = percent_change(last_fee, prev_fee)
    transaction_change = percent_change(last_total_transactions, prev_total_transactions)

    # =========================
    # FINAL RESPONSE (UI READY)
    # =========================
    return Response({
        "total_transaction_revenue": {
            "value": round(float(cur_total_revenue), 2),
            "change_percent": round(revenue_change, 2),
            "label": f"{round(revenue_change, 2)}% vs last month"
        },
        "total_platform_fees": {
            "value": round(float(cur_fee), 2),
            "change_percent": round(fee_change, 2),
            "label": f"{round(fee_change, 2)}% vs last month"
        },
        "total_transactions": {
            "value": cur_total_transactions,
            "change_percent": round(transaction_change, 2),
            "label": f"{round(transaction_change, 2)}% vs last month"
        }
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def stripe_all_payments(request):
    role_filter = request.GET.get("role", "").strip().lower()
    type_filter = request.GET.get("type", "").strip().lower()
    search = request.GET.get("search", "").strip().lower()
    download = request.GET.get("download", "").strip().lower()

    generic_start = request.GET.get("start_date")
    generic_end = request.GET.get("end_date")

    invoice_start = request.GET.get("invoice_start_date") or generic_start
    invoice_end = request.GET.get("invoice_end_date") or generic_end

    subscription_start = request.GET.get("subscription_start_date") or generic_start
    subscription_end = request.GET.get("subscription_end_date") or generic_end

    valid_roles = ["client", "landscaper"]
    valid_types = ["service", "subscription"]

    if role_filter and role_filter not in valid_roles:
        return Response(
            {
                "status": "error",
                "message": "Invalid role. Allowed values: client, landscaper."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if type_filter and type_filter not in valid_types:
        return Response(
            {
                "status": "error",
                "message": "Invalid type. Allowed values: service, subscription."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        invoice_start_dt, invoice_end_dt = parse_date_range(invoice_start, invoice_end)
        subscription_start_dt, subscription_end_dt = parse_date_range(subscription_start, subscription_end)
    except ValueError as e:
        return Response(
            {
                "status": "error",
                "message": str(e)
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = []

    # =========================
    # Client Service Payments (Invoice-based)
    # =========================
    if (not role_filter or role_filter == "client") and (not type_filter or type_filter == "service"):
        invoices = (
            Invoice.objects
            .select_related(
                "job",
                "job__client__user",
                "job__external_client",
                "job__landscaper",
            )
            .exclude(stripe_session_id__isnull=True)
            .exclude(stripe_session_id="")
        )

        if invoice_start_dt:
            invoices = invoices.filter(created_at__gte=invoice_start_dt)
        if invoice_end_dt:
            invoices = invoices.filter(created_at__lte=invoice_end_dt)

        for invoice in invoices:
            job = invoice.job

            if job.client:
                user_id = job.client.user.id
                name = job.client_name
                email = job.client_email
            elif job.external_client:
                user_id = None
                name = job.external_client.name
                email = job.external_client.email
            else:
                user_id = None
                name = None
                email = None

            data.append({
                "record_id": invoice.id,
                "user_id": user_id,
                "role": "client",
                "type": "service",
                "name": name,
                "email": email,
                "amount_paid": float(invoice.total or 0),
                "base_amount": float(invoice.subtotal or 0),
                "platform_fee": float(invoice.service_fee_amount or 0),
                "status": invoice.status,
                "transaction_id": invoice.stripe_session_id,
                "date": invoice.paid_at or invoice.created_at,
                "created_at": invoice.created_at,
                "job_id": job.id if job else None,
                "job_status": job.status if job else None,
                "invoice_number": invoice.invoice_number,
                "landscaper_id": job.landscaper.id if job and job.landscaper else None,
                "landscaper_name": job.landscaper.business_name if job and job.landscaper else None,
                "plan_id": None,
                "plan_name": None,
            })

    # =========================
    # Landscaper Subscription Payments
    # =========================
    if (not role_filter or role_filter == "landscaper") and (not type_filter or type_filter == "subscription"):
        subscriptions = (
            Subscription.objects
            .select_related("user", "plan")
            .exclude(stripe_subscription_id__isnull=True)
            .exclude(stripe_subscription_id="")
        )

        if subscription_start_dt:
            subscriptions = subscriptions.filter(created_at__gte=subscription_start_dt)
        if subscription_end_dt:
            subscriptions = subscriptions.filter(created_at__lte=subscription_end_dt)

        for sub in subscriptions:
            plan_price = float(sub.plan.price or 0) if sub.plan else 0.0

            if hasattr(sub, "discount_override") and sub.discount_override:
                amount_paid = plan_price - (plan_price * float(sub.discount_override) / 100)
            else:
                amount_paid = plan_price

            data.append({
                "record_id": sub.id,
                "user_id": sub.user.id if sub.user else None,
                "role": "landscaper",
                "type": "subscription",
                "name": getattr(sub.user, "name", None),
                "email": getattr(sub.user, "email", None),
                "amount_paid": round(amount_paid, 2),
                "base_amount": plan_price,
                "platform_fee": 0.0,
                "status": sub.status,
                "transaction_id": sub.stripe_subscription_id,
                "date": sub.created_at,
                "created_at": sub.created_at,
                "job_id": None,
                "job_status": None,
                "invoice_number": None,
                "landscaper_id": sub.user.id if sub.user else None,
                "landscaper_name": getattr(sub.user, "name", None),
                "plan_id": sub.plan.id if sub.plan else None,
                "plan_name": getattr(sub.plan, "name", None),
            })

    # =========================
    # Search filter
    # =========================
    if search:
        filtered_data = []

        for item in data:
            searchable_text = " ".join([
                str(item.get("name") or ""),
                str(item.get("email") or ""),
                str(item.get("invoice_number") or ""),
                str(item.get("transaction_id") or ""),
                str(item.get("plan_name") or ""),
                str(item.get("landscaper_name") or ""),
                str(item.get("status") or ""),
                str(item.get("type") or ""),
            ]).lower()

            if search in searchable_text:
                filtered_data.append(item)

        data = filtered_data

    # =========================
    # Sort latest first
    # =========================
    data.sort(
        key=lambda x: x["created_at"] if x["created_at"] else timezone.now(),
        reverse=True
    )

    # =========================
    # CSV
    # =========================
    if download == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payments_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Record ID",
            "User ID",
            "Role",
            "Type",
            "Name",
            "Email",
            "Amount Paid",
            "Base Amount",
            "Platform Fee",
            "Status",
            "Transaction ID",
            "Date",
            "Created At",
            "Job ID",
            "Job Status",
            "Invoice Number",
            "Plan ID",
            "Plan Name",
            "Landscaper ID",
            "Landscaper Name",
        ])

        for item in data:
            writer.writerow([
                item.get("record_id"),
                item.get("user_id"),
                item.get("role"),
                item.get("type"),
                item.get("name"),
                item.get("email"),
                item.get("amount_paid"),
                item.get("base_amount"),
                item.get("platform_fee"),
                item.get("status"),
                item.get("transaction_id"),
                item.get("date"),
                item.get("created_at"),
                item.get("job_id"),
                item.get("job_status"),
                item.get("invoice_number"),
                item.get("plan_id"),
                item.get("plan_name"),
                item.get("landscaper_id"),
                item.get("landscaper_name"),
            ])

        return response

    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(data, request)

    return paginator.get_paginated_response({
        "filters": {
            "role": role_filter or None,
            "type": type_filter or None,
            "search": search or None,
            "invoice_start_date": invoice_start,
            "invoice_end_date": invoice_end,
            "subscription_start_date": subscription_start,
            "subscription_end_date": subscription_end,
        },
        "results": result_page,
    })




# summary
def get_month_range(dt):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)

    return start, next_month


def percent_change(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_dashboard_summary(request):
    now = timezone.now()

    current_start, current_end = get_month_range(now)
    prev_anchor = current_start - timedelta(days=1)
    prev_start, prev_end = get_month_range(prev_anchor)

    # =========================
    # ALL TIME DATA
    # =========================
    all_invoices = Invoice.objects.exclude(
        stripe_session_id__isnull=True
    ).exclude(stripe_session_id="")

    total_revenue = all_invoices.aggregate(
        total=Sum("total")
    )["total"] or Decimal("0.00")

    total_fees = all_invoices.aggregate(
        total=Sum("service_fee_amount")
    )["total"] or Decimal("0.00")

    total_invoice_count = all_invoices.count()

    all_subscriptions = Subscription.objects.exclude(
        stripe_subscription_id__isnull=True
    ).exclude(stripe_subscription_id="")

    sub_revenue = Decimal("0.00")
    for sub in all_subscriptions:
        sub_revenue += Decimal(str(sub.plan.price or 0))

    total_transactions = total_invoice_count + all_subscriptions.count()
    total_revenue += sub_revenue

    # =========================
    # LAST MONTH
    # =========================
    last_invoices = all_invoices.filter(
        created_at__gte=prev_start,
        created_at__lt=prev_end
    )

    last_revenue = last_invoices.aggregate(
        total=Sum("total")
    )["total"] or Decimal("0.00")

    last_fees = last_invoices.aggregate(
        total=Sum("service_fee_amount")
    )["total"] or Decimal("0.00")

    last_invoice_count = last_invoices.count()

    last_subs = all_subscriptions.filter(
        created_at__gte=prev_start,
        created_at__lt=prev_end
    )

    last_sub_revenue = Decimal("0.00")
    for sub in last_subs:
        last_sub_revenue += Decimal(str(sub.plan.price or 0))

    last_total_transactions = last_invoice_count + last_subs.count()
    last_revenue += last_sub_revenue

    # =========================
    # PREVIOUS MONTH (for comparison)
    # =========================
    prev2_anchor = prev_start - timedelta(days=1)
    prev2_start, prev2_end = get_month_range(prev2_anchor)

    prev2_invoices = all_invoices.filter(
        created_at__gte=prev2_start,
        created_at__lt=prev2_end
    )

    prev2_revenue = prev2_invoices.aggregate(
        total=Sum("total")
    )["total"] or Decimal("0.00")

    prev2_fees = prev2_invoices.aggregate(
        total=Sum("service_fee_amount")
    )["total"] or Decimal("0.00")

    prev2_invoice_count = prev2_invoices.count()

    prev2_subs = all_subscriptions.filter(
        created_at__gte=prev2_start,
        created_at__lt=prev2_end
    )

    prev2_sub_revenue = Decimal("0.00")
    for sub in prev2_subs:
        prev2_sub_revenue += Decimal(str(sub.plan.price or 0))

    prev2_total_transactions = prev2_invoice_count + prev2_subs.count()
    prev2_revenue += prev2_sub_revenue

    # =========================
    # PERCENT CALCULATION
    # =========================
    revenue_change = percent_change(last_revenue, prev2_revenue)
    fee_change = percent_change(last_fees, prev2_fees)
    transaction_change = percent_change(last_total_transactions, prev2_total_transactions)

    return Response({
        "status": "success",
        "data": {
            "total_transaction_revenue": {
                "value": float(total_revenue),
                "last_month": float(last_revenue),
                "change_percent": round(revenue_change, 2)
            },
            "total_platform_fees": {
                "value": float(total_fees),
                "last_month": float(last_fees),
                "change_percent": round(fee_change, 2)
            },
            "total_transactions": {
                "value": total_transactions,
                "last_month": last_total_transactions,
                "change_percent": round(transaction_change, 2)
            }
        }
    })

# delete views
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
    job_qs = Job.objects.filter(
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
        landscaper = getattr(user, "landscaper_profile", None)

        if not landscaper:
            return Response(
                {"status": "error", "message": "No landscaper profile found."},
                status=404
            )

        current_year = timezone.now().year

        jobs = Job.objects.filter(
            landscaper=landscaper,
            is_active=True
        )

        # =========================
        # Monthly revenue (paid jobs in current year)
        # =========================
        monthly_revenue_qs = (
            jobs.filter(
                payment_status=Job.PaymentStatus.PAID,
                scheduled_date__year=current_year
            )
            .annotate(month=TruncMonth("scheduled_date"))
            .values("month")
            .annotate(
                total_amount=Coalesce(
                    Sum("total_price"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            )
            .order_by("month")
        )

        monthly_revenue = OrderedDict()
        for month in range(1, 13):
            monthly_revenue[f"{current_year}-{month:02d}"] = 0.0

        for item in monthly_revenue_qs:
            month_str = item["month"].strftime("%Y-%m")
            monthly_revenue[month_str] = round(float(item["total_amount"] or 0), 2)

        # =========================
        # Yearly revenue
        # =========================
        yearly_revenue = (
            jobs.filter(
                payment_status=Job.PaymentStatus.PAID,
                scheduled_date__year=current_year
            )
            .aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            )["total"]
            or 0
        )

        # =========================
        # Total revenue (all time)
        # =========================
        total_revenue = (
            jobs.filter(payment_status=Job.PaymentStatus.PAID)
            .aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            )["total"]
            or 0
        )

        # =========================
        # Pending payments
        # =========================
        pending_amount = (
            jobs.filter(payment_status=Job.PaymentStatus.PENDING)
            .aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            )["total"]
            or 0
        )

        # =========================
        # Extra useful stats
        # =========================
        paid_jobs_count = jobs.filter(payment_status=Job.PaymentStatus.PAID).count()
        pending_jobs_count = jobs.filter(payment_status=Job.PaymentStatus.PENDING).count()
        completed_jobs_count = jobs.filter(status=Job.Status.COMPLETED).count()

        data = {
            "status": "success",
            "data": {
                "monthly_revenue": [
                    {"month": month, "total_amount": total}
                    for month, total in monthly_revenue.items()
                ],
                "yearly_revenue": round(float(yearly_revenue), 2),
                "total_revenue": round(float(total_revenue), 2),
                "pending_amount": round(float(pending_amount), 2),
                "paid_jobs_count": paid_jobs_count,
                "pending_jobs_count": pending_jobs_count,
                "completed_jobs_count": completed_jobs_count,
            }
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
        stripe_payments = Job.objects.filter(
            payment_status=PaymentStatus.PAID
        ).exclude(stripe_payment_id__isnull=True).exclude(stripe_payment_id__exact='')

        stripe_total = stripe_payments.aggregate(
            total=Sum(F("service__price"), output_field=FloatField())
        )["total"] or 0.0

        # --------------------------
        # Cash payments
        # --------------------------
        cash_payments = Job.objects.filter(
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