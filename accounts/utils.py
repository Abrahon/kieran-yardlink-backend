
import logging
import smtplib
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def generate_otp():
    import random
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp_code, name="User", sender_name=None):
    subject = "🔐 Your OTP Code for Verification"

    html_content = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:20px auto;
                border:1px solid #e2e2e2;padding:20px;border-radius:10px;background-color:#f9f9f9;">
        <h2 style="color:#2c3e50;">Hello {name} 👋,</h2>
        <p>Your OTP code is:</p>
        <h1 style="color:#28a745;">{otp_code}</h1>
        <p>This OTP is valid for 5 minutes.</p>
    </div>
    """

    plain_text = strip_tags(html_content)

    # ✅ FIXED
    
    # sender_name = invoice.job.landscaper.user.get_full_name() or "Landscaper"
    from_email = f"{sender_name or 'System'} <{settings.EMAIL_HOST_USER}>"

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=from_email,
            to=[to_email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        logger.info("OTP email sent to %s", to_email)
        return True

    except (smtplib.SMTPException, ConnectionRefusedError, BadHeaderError) as exc:
        logger.exception("Failed sending OTP to %s: %s", to_email, exc)
        return False

    except Exception as exc:
        logger.exception("Unexpected error sending OTP to %s: %s", to_email, exc)
        return False

# role checking utilities
# TODO 
def is_landscaper(user):
    return user.role == "landscaper"


def is_phone_required(user):
    return user.role == "landscaper"