# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job
from profiles.models import LandscaperProfilies, ClientProfile
from notifications.utils import send_push_notification
from subscriptions.models import Subscription

# ------------------------
# Test Task
# ------------------------
@shared_task
def test_task():
    print("Celery is working!")
    return "OK"

# ------------------------
# Job Reminder (Landscaper)
# ------------------------
@shared_task
def send_job_reminders():
    now = timezone.now()
    upcoming_jobs = Job.objects.filter(
        is_completed=False,
        scheduled_date=now.date(),
        scheduled_time__gte=now.time(),
        scheduled_time__lte=(now + timedelta(hours=1)).time()
    )

    for job in upcoming_jobs:
        landscaper_profile = getattr(job.landscaper, "landscaperprofilies", None)
        if landscaper_profile and landscaper_profile.job_reminder:
            title = "Job Reminder"
            message = f"Reminder: Your job '{job.service.name}' is scheduled at {job.scheduled_time} today."
            send_push_notification(job.landscaper, title, message, notification_type="job")

# ------------------------
# Client Service Reminder
# ------------------------
@shared_task
def send_client_service_reminders():
    now = timezone.now()
    upcoming_services = Job.objects.filter(
        is_completed=False,
        scheduled_date=now.date(),
        scheduled_time__gte=now.time(),
        scheduled_time__lte=(now + timedelta(hours=1)).time()
    )

    for job in upcoming_services:
        client_profile = getattr(job.client, "clientprofile", None)
        if client_profile and client_profile.service_reminder:
            title = "Service Reminder"
            message = f"Reminder: Your service '{job.service.name}' is scheduled at {job.scheduled_time} today."
            send_push_notification(job.client, title, message, notification_type="service")

# ------------------------
# Completed Service Notification
# ------------------------
@shared_task
def send_completed_service_notifications():
    now = timezone.now()
    recent_completed = Job.objects.filter(
        is_completed=True,
        completed_at__gte=now - timedelta(minutes=5)  # last 5 minutes
    )

    for job in recent_completed:
        # Client notification
        client_profile = getattr(job.client, "clientprofile", None)
        if client_profile and client_profile.service_reminder:
            title = "Service Completed"
            message = f"Your service '{job.service.name}' was completed at {job.completed_at}."
            send_push_notification(job.client, title, message, notification_type="service")

        # Landscaper notification
        landscaper_profile = getattr(job.landscaper, "landscaperprofilies", None)
        if landscaper_profile and landscaper_profile.job_reminder:
            title = "Job Completed"
            message = f"Job '{job.service.name}' was completed at {job.completed_at}."
            send_push_notification(job.landscaper, title, message, notification_type="job")




# subscription notifications alerting users about trial ending
@shared_task
def send_trial_notifications():
    now = timezone.now()

    subs = Subscription.objects.filter(
        is_trial=True,
        is_active=True
    )

    for sub in subs:
        # days_left = (sub.trial_end_date - now).days
        days_left = max(       
            0,
            int((sub.trial_end_date - now).total_seconds() // 86400)
        )


        # ❌ expired trial → handle here
        if days_left < 0 and sub.is_active:
            sub.is_active = False
            sub.status = "expired"
            sub.save(update_fields=["is_active", "status"])
            continue

        # 🔔 5–1 day notifications
        if 1 <= days_left <= 5:
            if days_left not in sub.trial_notified_days:

                send_push_notification(
                    user=sub.user,
                    title="Trial Ending Soon",
                    message=f"{days_left} day(s) left in your trial",
                    notification_type="payment",
                )

                sub.trial_notified_days.append(days_left)
                sub.save(update_fields=["trial_notified_days"])

        # ⚠️ last day
        if days_left == 0 and not sub.last_day_notified:

            send_push_notification(
                user=sub.user,
                title="Trial Ends Today",
                message="Your trial expires today.",
                notification_type="payment",
            )

            sub.last_day_notified = True
            sub.save(update_fields=["last_day_notified"])