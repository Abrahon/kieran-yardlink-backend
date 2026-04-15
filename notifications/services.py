from firebase_admin import messaging
from notifications.models import Notification, Device


def send_push_notification(user, title, message, notification_type="job", data=None):
    """
    Production-ready notification sender
    """

    # 1. Check user settings
    settings = getattr(user, "notification_settings", None)

    if settings:
        if notification_type == "job" and not settings.job_alert:
            return None
        if notification_type == "payment" and not settings.payment_alert:
            return None
        if notification_type == "weather" and not settings.weather_alert:
            return None

    # 2. Save in DB
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

    # 3. Get active devices
    devices = Device.objects.filter(user=user, is_active=True)

    if not devices.exists():
        return notification

    tokens = [d.token for d in devices]

    # 4. Send FCM
    message_obj = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=message,
        ),
        tokens=tokens,
        data=data or {}
    )

    response = messaging.send_multicast(message_obj)

    # 5. Handle invalid tokens (VERY IMPORTANT)
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            devices[idx].is_active = False
            devices[idx].save(update_fields=["is_active"])

    return notification