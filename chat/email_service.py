import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_email(subject, html_content, to_email):
    """
    Universal email sender (works across all apps)
    """

    if not html_content:
        html_content = "<p>No content provided</p>"

    plain_text = strip_tags(html_content)

    from_email = settings.EMAIL_HOST_USER  # ALWAYS SAFE for SMTP

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=from_email,
            to=[to_email],
            reply_to=[from_email],
        )

        msg.attach_alternative(html_content, "text/html")
        msg.send()

        logger.info("Email sent to %s", to_email)
        return True

    except Exception as e:
        logger.exception("Email sending failed: %s", str(e))
        return False