# core/celery.py
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Create Celery app
app = Celery("core")

# Load config from Django settings (CELERY_*)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Schedule tasks using django-celery-beat or directly
app.conf.beat_schedule = {
    "completed-service-notifications": {
        "task": "notifications.tasks.send_completed_service_notifications",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
    "job-reminders": {
        "task": "notifications.tasks.send_job_reminders",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
    "client-service-reminders": {
        "task": "notifications.tasks.send_client_service_reminders",
        "schedule": crontab(minute="*/5"),  # every 5 minutes
    },
}

# Optional: make the app accessible via import
__all__ = ("app",)