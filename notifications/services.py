from firebase_admin import messaging
from notifications.models import Notification, Device


def send_push_notification(user, title, message, notification_type="job", data=None):

    print("🔥 send_push_notification CALLED")

    # -----------------------------
    # FIX: ensure real User object
    # -----------------------------
    if hasattr(user, "user"):
        user = user.user

    if not user:
        print("❌ USER IS NONE")
        return None

    print("✅ FINAL USER:", user)

    # -----------------------------
    # 1. Notification Settings Check
    # -----------------------------
    settings = getattr(user, "notification_settings", None)

    if settings:
        if notification_type == "job" and not settings.job_alert:
            print("❌ BLOCKED BY SETTINGS (job)")
            return None
        if notification_type == "payment" and not settings.payment_alert:
            print("❌ BLOCKED BY SETTINGS (payment)")
            return None
        if notification_type == "weather" and not settings.weather_alert:
            print("❌ BLOCKED BY SETTINGS (weather)")
            return None

    # -----------------------------
    # 2. SAVE NOTIFICATION (DB)
    # -----------------------------
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

    print("💾 NOTIFICATION SAVED:", notification.id)

    # -----------------------------
    # 3. GET DEVICES
    # -----------------------------
    devices = Device.objects.filter(user=user, is_active=True)

    if not devices.exists():
        print("❌ NO DEVICES FOUND")
        return notification

    tokens = [d.token for d in devices]

    # -----------------------------
    # 4. FIREBASE PUSH
    # -----------------------------
    message_obj = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=message,
        ),
        tokens=tokens,
        data={k: str(v) for k, v in (data or {}).items()}
    )

    response = messaging.send_multicast(message_obj)

    print("📡 FCM SENT:", response.success_count)

    return notification