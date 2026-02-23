from rest_framework import serializers
from .models import Notification, NotificationSettings

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "message", "is_read", "created_at"]

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ["job_alert", "payment_alert", "weather_alert"]
