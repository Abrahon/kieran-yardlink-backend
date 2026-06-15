from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def get_invoice_recipient(invoice):
    job = invoice.job

    # external client FIRST (because they pay from email)
    if job.external_client and job.external_client.email:
        return job.external_client.email, True

    # internal client
    if job.client and job.client.user and job.client.user.email:
        return job.client.user.email, False

    return None, False

    
def get_job_recipient_name(job):
    if not job:
        return "Client"

    # External client
    if getattr(job, "external_client", None):
        if job.external_client.name:
            return job.external_client.name

    # App client
    client = getattr(job, "client", None)
    if client:
        user = getattr(client, "user", None)

        # Prefer real user name first
        if user:
            if getattr(user, "name", None):
                return user.name

            name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            if name:
                return name

            if getattr(user, "username", None):
                return user.username

            if getattr(user, "email", None):
                return user.email

        # Fallback to client profile name only if useful
        if getattr(client, "name", None) and client.name != "Client":
            return client.name

    return "Client"



def send_invoice_email(invoice, frontend_invoice_url=None):
    client_email, is_external = get_invoice_recipient(invoice)

    if not client_email:
        raise ValueError("Client email not found.")

    recipient_name = get_job_recipient_name(invoice.job)

    subject = f"Invoice {invoice.invoice_number} for completed job"

    context = {
        "invoice": invoice,
        "job": invoice.job,
        "recipient_name": recipient_name,
        "line_items": invoice.line_items.all(),
        "pay_url": invoice.stripe_checkout_url if is_external else None,
        "frontend_invoice_url": frontend_invoice_url,
        "is_external_client": is_external,
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