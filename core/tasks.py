from notifications.services import send_push_notification

from celery import shared_task
from django.utils import timezone
from jobs.models import Job
from datetime import timedelta, datetime
from django.utils import timezone
from datetime import timedelta



def send_weather_alert(user):
    send_push_notification(
        user=user,
        title="Weather Alert",
        message="Heavy rain expected today",
        notification_type="weather",
        data={"screen": "weather"}
    )





@shared_task
def send_job_reminders():

    now = timezone.now()

    # 🎯 exactly 1 hour later
    target = now + timedelta(hours=1)

    start_window = target - timedelta(minutes=5)
    end_window = target + timedelta(minutes=5)

    jobs = Job.objects.filter(
        status=Job.Status.UPCOMING
    ).select_related("landscaper", "client")

    for job in jobs:

        job_datetime = datetime.combine(
            job.scheduled_date,
            job.scheduled_time
        )

        # 🔥 IMPORTANT FIX: make timezone-aware properly
        job_datetime = timezone.make_aware(job_datetime, timezone.get_current_timezone())

        if start_window <= job_datetime <= end_window:

            # 🚫 prevent duplicate notifications (VERY IMPORTANT)
            if getattr(job, "reminder_sent", False):
                continue

            # 🔥 LANDSCAPER ONLY (your requirement)
            if job.landscaper:

                send_push_notification(
                    user=job.landscaper.user,
                    title="⏰ Job starts in 1 hour",
                    message=f"Job #{job.id} will start soon. Prepare yourself.",
                    notification_type="job",
                    data={
                        "job_id": job.id,
                        "type": "reminder"
                    }
                )

                # mark as sent (you MUST add this field OR use another method)
                job.reminder_sent = True
                job.save(update_fields=["reminder_sent"])