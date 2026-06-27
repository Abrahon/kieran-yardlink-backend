
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
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:#f4f4f4;padding:30px 0;">
        <tr>
            <td align="center">

                <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
                       style="background:#ffffff;
                              border-radius:12px;
                              padding:40px;
                              border:1px solid #e5e5e5;
                              text-align:center;
                              font-family:Arial,sans-serif;">

                    <tr>
                        <td>

                            <h2 style="margin:0;color:#2c3e50;">
                                Hello {name} 👋
                            </h2>

                            <p style="margin-top:20px;
                                      font-size:16px;
                                      color:#555;">
                                Use the OTP below to complete your verification.
                            </p>

                            <div style="
                                display:inline-block;
                                margin:25px 0;
                                padding:15px 35px;
                                background:#28a745;
                                color:#ffffff;
                                font-size:34px;
                                font-weight:bold;
                                letter-spacing:8px;
                                border-radius:8px;
                            ">
                                {otp_code}
                            </div>

                            <p style="color:#666;font-size:15px;">
                                This OTP is valid for
                                <strong>5 minutes</strong>.
                            </p>

                            <hr style="margin:30px 0;border:none;border-top:1px solid #eeeeee;">

                            <p style="font-size:13px;color:#999;">
                                If you didn't request this OTP, you can safely ignore this email.
                            </p>

                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>
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