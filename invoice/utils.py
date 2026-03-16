from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_invoice_email(invoice, frontend_invoice_url=None):
    client_email = invoice.sent_to_email
    if not client_email:
        raise ValueError("Client email not found.")

    subject = f"Invoice {invoice.invoice_number} for completed job"

    context = {
        "invoice": invoice,
        "job": invoice.job,
        "client": invoice.job.client,
        "line_items": invoice.line_items.all(),
        "pay_url": invoice.stripe_checkout_url,
        "frontend_invoice_url": frontend_invoice_url,
    }

    text_body = render_to_string("emails/invoice_email.txt", context)
    html_body = render_to_string("emails/invoice_email.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        to=[client_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()