# from django.apps import AppConfig
# # import notifications.firebase

# class NotificationsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'notifications'

# notifications/apps.py
from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"