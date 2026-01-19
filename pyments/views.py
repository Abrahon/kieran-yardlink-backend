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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    user = request.user
    landscaper_id = request.data.get("landscaper_id")
    amount = int(float(request.data.get("amount")) * 100)  # convert to cents

    # Fetch the landscaper
    landscaper = LandscaperProfile.objects.get(id=landscaper_id)

    # Platform fee (optional)
    platform_fee = int(amount * 0.02)

    # Create a Stripe Checkout Session with auto-pay setup
    session = stripe.checkout.Session.create(
        mode="setup",  # setup mode for future payments
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        metadata={
            "client_id": user.id,
            "landscaper_id": landscaper.id,
            "amount": amount,
        },
        payment_intent_data={
            "setup_future_usage": "off_session",  
            "application_fee_amount": platform_fee,
            "transfer_data": {
                "destination": landscaper.stripe_account_id,
            }
        },
        success_url=f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/payment-cancelled",
    )

    return Response({"checkout_url": session.url})

# CASH PAYMENT

class CashPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = ServiceBooking.objects.get(id=booking_id, client=request.user)
        except ServiceBooking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=404)

        # Mark cash as pending
        booking.payment_status = "cash_pending"
        booking.save()

        return Response({
            "message": "Cash payment selected. Please pay the landscaper in person."
        })

