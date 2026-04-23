# import stripe
# from django.conf import settings


# def create_invoice_checkout_session(invoice):
#     """
#     Create Stripe Checkout Session for an invoice.
#     Returns the Stripe session object.
#     """
#     stripe.api_key = settings.STRIPE_SECRET_KEY

#     if not invoice.job or not invoice.job.client or not invoice.job.client.user:
#         raise ValueError("Invoice client information is missing.")

#     customer_email = invoice.job.client.user.email
#     invoice_total = invoice.total

#     if invoice_total is None or invoice_total <= 0:
#         raise ValueError("Invoice total must be greater than zero.")

#     unit_amount = int(invoice_total * 100)

#     session = stripe.checkout.Session.create(
#         payment_method_types=["card"],
#         mode="payment",
#         customer_email=customer_email,
#         line_items=[
#             {
#                 "price_data": {
#                     "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
#                     "unit_amount": unit_amount,
#                     "product_data": {
#                         "name": f"Invoice {invoice.invoice_number}",
#                         "description": f"Completed Job #{invoice.job.id}",
#                     },
#                 },
#                 "quantity": 1,
#             }
#         ],
#         success_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/success/?invoice_id={invoice.id}&session_id={{CHECKOUT_SESSION_ID}}",
#         cancel_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/payment-cancel?invoice_id={invoice.id}",
            
            
#         metadata={
#             "invoice_id": str(invoice.id),
#             "job_id": str(invoice.job.id),
#             "client_id": str(invoice.job.client.id),
#             "landscaper_id": str(invoice.job.landscaper.id),
#         },
#     )

#     return session


import stripe  
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP

def create_invoice_checkout_session(invoice):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer_email = invoice.sent_to_email
    if not customer_email:
        raise ValueError("Invoice recipient email is required.")

    if not invoice.total or invoice.total <= 0:
        raise ValueError("Invoice total must be greater than zero.")

    # unit_amount = int(invoice.total * 100)
    unit_amount = int(
    (Decimal(invoice.total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) * 100

    )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": f"Invoice {invoice.invoice_number}",
                        "description": f"Completed Job #{invoice.job.id}",
                    },
                },
                "quantity": 1,
            }
        ],
        # success_url=f"{settings.FRONTEND_URL}/payment-success?invoice_id={invoice.id}&session_id={{CHECKOUT_SESSION_ID}}",
        # cancel_url=f"{settings.FRONTEND_URL}/payment-cancel?invoice_id={invoice.id}",
        
        # success_url=f"https://api.yardlinkapp.com/success/?invoice_id={invoice.id}&session_id={{CHECKOUT_SESSION_ID}}",
        # cancel_url=f"https://api.yardlinkapp.com/api/payment-cancel?invoice_id={invoice.id}",
        
        success_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/success/?invoice_id={invoice.id}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/payment-cancel?invoice_id={invoice.id}",
        metadata={
            "invoice_id": str(invoice.id),
            "job_id": str(invoice.job.id),
            "landscaper_id": str(invoice.job.landscaper.id),
            "client_id": str(invoice.job.client.id) if getattr(invoice.job, "client", None) else "",
            "external_client_id": str(invoice.job.external_client.id) if getattr(invoice.job, "external_client", None) else "",
        },
    )

    return session