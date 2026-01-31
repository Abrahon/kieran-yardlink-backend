from django.shortcuts import render
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from landscapers.models import LandscaperProfile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bookings.models import ServiceBooking, BookingStatus
stripe.api_key = settings.STRIPE_SECRET_KEY


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def create_checkout_session(request):
#     user = request.user
#     landscaper_id = request.data.get("landscaper_id")
#     amount = int(float(request.data.get("amount")) * 100)  # convert to cents

#     # Fetch the landscaper
#     landscaper = LandscaperProfile.objects.get(id=landscaper_id)

#     # Platform fee (optional)
#     platform_fee = int(amount * 0.02)

#     # Create a Stripe Checkout Session with auto-pay setup
#     session = stripe.checkout.Session.create(
#         mode="setup",  # setup mode for future payments
#         customer=user.stripe_customer_id,
#         payment_method_types=["card"],
#         metadata={
#             "client_id": user.id,
#             "landscaper_id": landscaper.id,
#             "amount": amount,
#         },
#         payment_intent_data={
#             "setup_future_usage": "off_session",  
#             "application_fee_amount": platform_fee,
#             "transfer_data": {
#                 "destination": landscaper.stripe_account_id,
#             }
#         },
#         success_url=f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
#         cancel_url=f"{settings.FRONTEND_URL}/payment-cancelled",
#     )

#     return Response({"checkout_url": session.url})

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def create_checkout_session(request, booking_id):
#     try:
#         booking = ServiceBooking.objects.get(id=booking_id, client=request.user)
#     except ServiceBooking.DoesNotExist:
#         return Response({"error": "Booking not found."}, status=404)

#     amount = int(booking.agreed_price * 100)  # Stripe uses cents
#     platform_fee = int(amount * 0.02)
#     landscaper = booking.landscaper

#     session = stripe.checkout.Session.create(
#         payment_method_types=["card"],
#         mode="payment",
#         line_items=[{
#             "price_data": {
#                 "currency": "usd",
#                 "unit_amount": amount,
#                 "product_data": {
#                     "name": booking.service.name,
#                 },
#             },
#             "quantity": 1,
#         }],
#         payment_intent_data={
#             "application_fee_amount": platform_fee,   # platform fee
#             "transfer_data": {
#                 "destination": landscaper.stripe_account_id
#             },
#             "setup_future_usage": "off_session"       # save card for future payments
#         },
#         success_url=f"{settings.FRONTEND_URL}/payment-success?booking_id={booking.id}",
#         cancel_url=f"{settings.FRONTEND_URL}/payment-cancel?booking_id={booking.id}",
#         metadata={
#             "booking_id": booking.id,
#             "client_id": request.user.id,
#             "landscaper_id": landscaper.id
#         }
#     )

#     # Save Stripe session ID in booking
#     booking.stripe_payment_id = session.id
#     booking.save(update_fields=["stripe_payment_id"])

#     return Response({"checkout_url": session.url})



# CASH PAYMENT

# class CashPaymentAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, booking_id):
#         try:
#             booking = ServiceBooking.objects.get(id=booking_id, client=request.user)
#         except ServiceBooking.DoesNotExist:
#             return Response({"error": "Booking not found."}, status=404)

#         # Mark cash as pending
#         booking.payment_status = "cash_pending"
#         booking.save()

#         return Response({
#             "message": "Cash payment selected. Please pay the landscaper in person."
#         })


# # webhook
# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

#     if not sig_header:
#         return HttpResponse("Missing signature", status=400)

#     try:
#         event = stripe.Webhook.construct_event(
#             payload,
#             sig_header,
#             settings.STRIPE_WEBHOOK_SECRET
#         )
#     except stripe.error.SignatureVerificationError:
#         return HttpResponse("Invalid signature", status=400)
#     except Exception:
#         return HttpResponse("Webhook error", status=400)

#     if event["type"] == "checkout.session.completed":
#         session = event["data"]["object"]
#         metadata = session.get("metadata", {})

#         # ------------------ Booking Payment ------------------
#         booking_id = metadata.get("booking_id")
#         if booking_id:
#             from bookings.models import ServiceBooking, PaymentStatus

#             try:
#                 booking = ServiceBooking.objects.get(id=booking_id)
#                 booking.payment_status = PaymentStatus.PAID
#                 booking.save(update_fields=["payment_status"])
#             except ServiceBooking.DoesNotExist:
#                 return HttpResponse("Booking not found", status=400)

#         # ------------------ Subscription Payment ------------------
#         user_id = metadata.get("user_id")
#         plan_id = metadata.get("plan_id")
#         stripe_subscription_id = session.get("subscription")

#         if user_id and plan_id and stripe_subscription_id:
#             from django.contrib.auth import get_user_model
#             from subscriptions.models import Plan, Subscription
#             from django.utils import timezone
#             from datetime import timedelta

#             User = get_user_model()
#             user = User.objects.filter(id=user_id).first()
#             plan = Plan.objects.filter(id=plan_id).first()

#             if not user or not plan:
#                 return HttpResponse("Invalid user or plan", status=400)

#             # Prevent duplicate subscriptions
#             if not Subscription.objects.filter(
#                 stripe_subscription_id=stripe_subscription_id
#             ).exists():
#                 Subscription.objects.create(
#                     user=user,
#                     plan=plan,
#                     stripe_subscription_id=stripe_subscription_id,
#                     start_date=timezone.now(),
#                     end_date=timezone.now() + timedelta(days=plan.duration_days),
#                     status="active"
#                 )

#                 # Upgrade role
#                 user.role = "landscaper"
#                 user.save(update_fields=["role"])

#     return HttpResponse(status=200)




# views.py
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bookings.models import ServiceBooking, BookingStatus
from .models import ServiceSchedule
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_checkout_session(request, schedule_id):
    """
    Client pays for a completed job (ServiceSchedule)
    """
    from bookings.models import PaymentStatus  # optional, if you use a PaymentStatus enum

    try:
        schedule = ServiceSchedule.objects.get(
            id=schedule_id,
            client=request.user.clientprofile
        )
    except ServiceSchedule.DoesNotExist:
        return Response({"error": "Schedule not found."}, status=404)

    if not schedule.is_completed:
        return Response({"error": "Job is not yet completed."}, status=400)

    # Amount in cents
    amount = int(schedule.service.price * 100)

    # Platform fee (2%)
    platform_fee = int(amount * 0.02)

    # Get landscaper account
    landscaper = schedule.landscaper

    # Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": amount,
                "product_data": {
                    "name": schedule.service.name,
                },
            },
            "quantity": 1,
        }],
        payment_intent_data={
            "application_fee_amount": platform_fee,
            "transfer_data": {
                "destination": landscaper.stripe_account_id
            },
            "setup_future_usage": "off_session"  # saves card for future auto payment
        },
        success_url=f"{settings.FRONTEND_URL}/payment-success?schedule_id={schedule.id}",
        cancel_url=f"{settings.FRONTEND_URL}/payment-cancel?schedule_id={schedule.id}",
        metadata={
            "schedule_id": schedule.id,
            "client_id": request.user.id,
            "landscaper_id": landscaper.id
        }
    )

    # Save Stripe session ID
    schedule.stripe_payment_id = session.id
    schedule.save(update_fields=["stripe_payment_id"])

    return Response({"checkout_url": session.url})
class CashPaymentScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, schedule_id):
        try:
            schedule = ServiceSchedule.objects.get(id=schedule_id, client=request.user.clientprofile)
        except ServiceSchedule.DoesNotExist:
            return Response({"error": "Schedule not found."}, status=404)

        # Mark cash as pending
        schedule.payment_status = "cash_pending"
        schedule.save(update_fields=["payment_status"])

        return Response({
            "message": "Cash payment selected. Please pay the landscaper in person."
        })
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not sig_header:
        return HttpResponse("Missing signature", status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)
    except Exception:
        return HttpResponse("Webhook error", status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})

        schedule_id = metadata.get("schedule_id")
        if schedule_id:
            from bookings.models import ServiceSchedule, PaymentStatus
            try:
                schedule = ServiceSchedule.objects.get(id=schedule_id)
                schedule.payment_status = PaymentStatus.PAID
                schedule.save(update_fields=["payment_status"])
            except ServiceSchedule.DoesNotExist:
                return HttpResponse("Schedule not found", status=400)

    return HttpResponse(status=200)
