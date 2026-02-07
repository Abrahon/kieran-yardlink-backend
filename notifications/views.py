from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification, NotificationSettings
from .serializers import NotificationSerializer, NotificationSettingsSerializer
from firebase_admin import messaging

class NotificationListView(APIView):
    """
    Get all notifications for the logged-in Pro landscaper.
    Supports optional 'unread' filter via query param.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread = request.query_params.get("unread")  # Get query param
        notifications = Notification.objects.filter(user=request.user)
        if unread == "true":
            notifications = notifications.filter(is_read=False)  # Filter unread messages
        serializer = NotificationSerializer(notifications, many=True)
        return Response({"notifications": serializer.data})


class NotificationSettingsView(APIView):
    """
    Get or update notification preferences.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings, _ = NotificationSettings.objects.get_or_create(user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)

    def post(self, request):
        settings, _ = NotificationSettings.objects.get_or_create(user=request.user)
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_push_notification(user, title, message, notification_type):
    settings = getattr(user, "notification_settings", None)
    if not settings:
        return

    # Check if notifications are enabled
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

    # Send FCM push
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
