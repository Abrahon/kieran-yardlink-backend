from django.urls import path
from .views import (
    NotificationListView,
    NotificationSettingsView,
    RecentCompletedNotificationsAPIView,
    NotificationReadAPIView,
    save_fcm_token,
    TestNotificationAPIView,
    remove_fcm_token,
    mark_notification_read,
    mark_all_notifications_read
)

urlpatterns = [
    path("save-fcm-token/", save_fcm_token),

    path("notifications/", NotificationListView.as_view()),
    path("notifications/<int:id>/read/", mark_notification_read, name="notification-read"),
    path("notifications/read-all/", mark_all_notifications_read, name="notifications-read-all"),
    path("notifications/settings/", NotificationSettingsView.as_view()),
    path("notifications/recent-completed/", RecentCompletedNotificationsAPIView.as_view()),
    path("remove-token/", remove_fcm_token, name="remove-fcm-token"),

    path("notifications/<int:notification_id>/read/", NotificationReadAPIView.as_view()),
    path("test/", TestNotificationAPIView.as_view(), name="test-notification"),
]