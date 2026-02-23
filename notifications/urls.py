from django.urls import path
from .views import NotificationListView, NotificationSettingsView,RecentCompletedNotificationsAPIView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/settings/", NotificationSettingsView.as_view(), name="notifications-settings"),
    path("notifications/recent-completed/", RecentCompletedNotificationsAPIView.as_view(), name="recent-completed-notifications"),
]
