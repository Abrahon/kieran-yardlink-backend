from django.urls import path
from .views import NotificationListView, NotificationSettingsView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/settings/", NotificationSettingsView.as_view(), name="notifications-settings"),
]
