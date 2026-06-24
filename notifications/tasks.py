# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job
from profiles.models import LandscaperProfilies, ClientProfile
from notifications.utils import send_push_notification
from subscriptions.models import Subscription
from accounts.models import User
from jobs.models import JobItem
from datetime import datetime, timedelta



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

    jobs = Job.objects.filter(
        status=Job.Status.UPCOMING,
        scheduled_date=now.date()
    ).select_related("landscaper__user", "client")

    for job in jobs:

        if not job.scheduled_date or not job.scheduled_time:
            continue

        job_datetime = timezone.make_aware(
            datetime.combine(job.scheduled_date, job.scheduled_time),
            timezone.get_current_timezone()
        )

        diff = job_datetime - now

        # ------------------
        # 1 HOUR REMINDER
        # ------------------
        if timedelta(hours=0, minutes=55) <= diff <= timedelta(hours=1, minutes=5):

            if not job.reminder_sent_at:
                send_push_notification(
                    user=job.landscaper.user,
                    title="⏰ Job in 1 hour",
                    message=f"Job #{job.id} starts at {job.scheduled_time}",
                    notification_type="job"
                )

                job.reminder_sent_at = now
                job.save(update_fields=["reminder_sent_at"])


        # ------------------
        # 30 MIN REMINDER
        # ------------------
        elif timedelta(minutes=25) <= diff <= timedelta(minutes=35):

            if job.reminder_sent_at:  # already 1h sent
                send_push_notification(
                    user=job.landscaper.user,
                    title="⏰ Job in 30 minutes",
                    message=f"Job #{job.id} starting soon",
                    notification_type="job"
                )

# ------------------------
# Client Service Reminder
# ------------------------
@shared_task
def send_client_service_reminders():
    now = timezone.now()

    upcoming_jobs = Job.objects.filter(
        status=Job.Status.UPCOMING,
        scheduled_date=now.date()
    ).select_related("client__user")

    for job in upcoming_jobs:

        has_incomplete = job.items.filter(is_completed=False).exists()

        if not has_incomplete:
            continue

        first_item = job.items.filter(is_completed=False).first()

        service_name = (
            first_item.service.name
            if first_item and first_item.service
            else "Service"
        )

        send_push_notification(
            user=job.client.user,   # ✅ FIXED
            title="Service Reminder",
            message=f"Reminder: '{service_name}' at {job.scheduled_time}",
            notification_type="service"
        )


# ------------------------
# Completed Service Notification
# ------------------------
@shared_task
def send_completed_service_notifications():
    now = timezone.now()
    recent_completed = JobItem.objects.filter(
        is_completed=True,
        completed_at__gte=now - timedelta(minutes=5)
    ).select_related("job", "job__client", "job__landscaper")

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



@shared_task
def send_weather_alerts():
    users = User.objects.filter(notification_settings__weather_alert=True)

    # fake example (replace with real API)
    weather_alert = {
        "is_severe": True,
        "message": "Heavy rain expected today 🌧"
    }

    if weather_alert["is_severe"]:
        for user in users:
            send_push_notification(
                user=user,
                title="Weather Alert 🌧",
                message=weather_alert["message"],
                notification_type="weather"
            )