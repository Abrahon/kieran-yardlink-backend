# notifications/utils.py
from notifications.models import Notification, NotificationSettings
from django.core.mail import send_mail
from firebase_admin import messaging

def send_email_notification(user, title, message):
    send_mail(
        title,
        message,
        "no-reply@yourapp.com",
        [user.email],
        fail_silently=False
    )

def send_push_notification(user, title, message, notification_type="job", send_email=False):
    """
    Sends notification respecting user settings.
    """
    # Check user settings
    settings = getattr(user, "notification_settings", None)
    if settings:
        if notification_type == "job" and not settings.job_alert:
            return
        if notification_type == "payment" and not settings.payment_alert:
            return
        if notification_type == "weather" and not settings.weather_alert:
            return

    # Create notification record
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message
    )

    # Optional email
    if send_email:
        send_email_notification(user, title, message)

    # Optional FCM push
    if hasattr(user, "fcm_token") and user.fcm_token:
        messaging.send(
            messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message
                ),
                token=user.fcm_token
            )
        )