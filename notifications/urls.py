from django.urls import path
from .views import (
    NotificationListView,
    NotificationSettingsView,
    RecentCompletedNotificationsAPIView,
    NotificationReadAPIView,
    save_fcm_token,
    TestNotificationAPIView
)

urlpatterns = [
    path("save-fcm-token/", save_fcm_token),

    path("notifications/", NotificationListView.as_view()),
    path("notifications/settings/", NotificationSettingsView.as_view()),
    path("notifications/recent-completed/", RecentCompletedNotificationsAPIView.as_view()),

    path("notifications/<int:notification_id>/read/", NotificationReadAPIView.as_view()),
    path("test/", TestNotificationAPIView.as_view(), name="test-notification"),
]