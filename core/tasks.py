from notifications.services import send_push_notification

def send_weather_alert(user):
    send_push_notification(
        user=user,
        title="Weather Alert",
        message="Heavy rain expected today",
        notification_type="weather",
        data={"screen": "weather"}
    )