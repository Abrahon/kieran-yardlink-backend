# core/celery.py

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
# CELERY BEAT SCHEDULE
# =========================
app.conf.beat_schedule = {
    
    # 🟢 Job reminders (every 5 minutes check upcoming jobs)
    "job-reminders": {
        "task": "notifications.tasks.send_job_reminders",
        "schedule": crontab(minute="*/5"),
    },

    # 🟢 Payment follow-ups / failed payments / logs (optional background check)
    "payment-checks": {
        "task": "notifications.tasks.send_payment_followups",
        "schedule": crontab(minute="*/10"),
    },

    # 🟢 Weather alerts
    "weather-alerts": {
        "task": "notifications.tasks.send_weather_alerts",
        "schedule": crontab(minute="*/15"),
    },

    # 🟢 Trial / subscription checks
    "trial-notifications-daily": {
        "task": "notifications.tasks.send_trial_notifications",
        "schedule": crontab(hour=9, minute=0),
    },
}

__all__ = ("app",)