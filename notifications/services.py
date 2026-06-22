

from firebase_admin import messaging
from notifications.models import Notification, Device


def send_push_notification(user, title, message, notification_type="job", data=None):

    print("🔥 send_push_notification CALLED")

    # -----------------------------
    # FIX USER OBJECT
    # -----------------------------
    if hasattr(user, "user"):
        user = user.user

    if not user:
        print("❌ USER IS NONE")
        return None

    print("✅ FINAL USER:", user)

    # -----------------------------
    # NOTIFICATION SETTINGS CHECK
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
    # DUPLICATE CHECK (ADD THIS)
    # -----------------------------
    exists = Notification.objects.filter(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message
    ).exists()

    if exists:
        print("⚠️ DUPLICATE NOTIFICATION BLOCKED")
        return None

    # -----------------------------
    # SAVE NOTIFICATION
    # -----------------------------
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

    print("💾 NOTIFICATION SAVED:", notification.id)

    # -----------------------------
    # DEVICES
    # -----------------------------
    tokens = list(
        Device.objects.filter(user=user, is_active=True)
        .exclude(token__isnull=True)
        .exclude(token__exact="")
        .values_list("token", flat=True)
    )

    if not tokens:
        print("❌ NO DEVICES FOUND")
        return notification

    print("📱 TOKENS:", len(tokens))

    # -----------------------------
    # FIREBASE MESSAGE
    # -----------------------------
    try:
        multicast_message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            tokens=tokens,
            data={k: str(v) for k, v in (data or {}).items()}
        )

        response = messaging.send_each_for_multicast(multicast_message)

        print("📡 FCM SENT SUCCESS:", response.success_count)
        print("📡 FCM FAILED:", response.failure_count)

    except Exception as e:
        print("🔥 FCM ERROR:", str(e))

    return notification