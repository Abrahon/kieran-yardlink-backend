from firebase_admin import messaging
from notifications.models import Notification, Device


def send_push_notification(user, title, message, notification_type="job", data=None):

    # 1. Check settings
    settings = getattr(user, "notification_settings", None)

    if settings:
        if notification_type == "job" and not settings.job_alert:
            return None
        if notification_type == "payment" and not settings.payment_alert:
            return None
        if notification_type == "weather" and not settings.weather_alert:
            return None

    # 2. Save DB notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

    # 3. Devices
    devices = Device.objects.filter(user=user, is_active=True)

    if not devices.exists():
        return notification

    device_map = {d.token: d for d in devices}
    tokens = list(device_map.keys())

    if not tokens:
        return notification

    # 4. FCM payload
    message_obj = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=message,
        ),
        tokens=tokens,
        data={k: str(v) for k, v in (data or {}).items()}
    )

    response = messaging.send_multicast(message_obj)

    # 5. Safe cleanup
    for idx, resp in enumerate(response.responses):
        token = tokens[idx]

        if not resp.success:
            device = device_map.get(token)
            if device:
                device.is_active = False
                device.save(update_fields=["is_active"])

    return notification