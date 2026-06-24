import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Load Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto discover tasks
app.autodiscover_tasks()

# =========================
# IMPORTANT SETTINGS
# =========================
app.conf.enable_utc = True
app.conf.timezone = "UTC"

# =========================
# CELERY BEAT SCHEDULE
# =========================
app.conf.beat_schedule = {
    
    "job-reminders": {
        "task": "notifications.tasks.send_job_reminders",
        "schedule": crontab(minute="*/5"),
    },

    "payment-checks": {
        "task": "notifications.tasks.send_payment_followups",
        "schedule": crontab(minute="*/10"),
    },

    "weather-alerts": {
        "task": "notifications.tasks.send_weather_alerts",
        "schedule": crontab(minute="*/15"),
    },

    "trial-notifications-daily": {
        "task": "notifications.tasks.send_trial_notifications",
        "schedule": crontab(hour=9, minute=0),
    },
    "expire-jobs": {
    "task": "notifications.tasks.update_expired_jobs",
    "schedule": crontab(minute="*/1"),
},
}

__all__ = ("app",)