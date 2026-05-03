from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification, NotificationSettings
from .serializers import NotificationSerializer, NotificationSettingsSerializer
from firebase_admin import messaging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification
from notifications.serializers import NotificationSerializer

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
# notifications/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from notifications.models import Notification, NotificationSettings
from notifications.serializers import NotificationSerializer, NotificationSettingsSerializer
from firebase_admin import messaging  # If you use FCM
from rest_framework.decorators import api_view, permission_classes
from .models import Device

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all notifications for the logged-in user.
        Optional query param: ?unread=true
        """
        unread = request.query_params.get("unread") == "true"
        notifications = Notification.objects.filter(user=request.user)
        if unread:
            notifications = notifications.filter(is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response({"notifications": serializer.data})


class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the user's notification preferences.
        """
        settings, _ = NotificationSettings.objects.get_or_create(user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)

    def post(self, request):
        """
        Update the user's notification preferences.
        """
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

# notifications/views.py
class UserNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all notifications for logged-in user
        """
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def patch(self, request, notification_id):
        """
        Mark a notification as read
        """
        notification = Notification.objects.filter(id=notification_id, user=request.user).first()
        if not notification:
            return Response({"detail": "Notification not found"}, status=404)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"detail": "Notification marked as read"})




class RecentCompletedNotificationsAPIView(APIView):
    """
    Returns recent completed service/job notifications for the logged-in user.
    Supports optional 'limit' query param (default 10).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        notifications = Notification.objects.filter(
            user=request.user,
            notification_type="job",  # only completed job/service notifications
            is_read=False  # optional: filter unread
        ).order_by("-created_at")[:limit]

        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            "count": notifications.count(),
            "notifications": serializer.data
        })

# .....




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "Token required"}, status=400)

    # Create or update device
    Device.objects.update_or_create(
        token=token,
        defaults={
            "user": request.user,
            "is_active": True
        }
    )

    return Response({"message": "Token saved"})



from notifications.utils import send_push_notification

class TestNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        send_push_notification(
            user=request.user,
            title="Test Notification",
            message="This is a test push 🔥",
            notification_type="job"
        )
        return Response({"message": "Notification sent"})