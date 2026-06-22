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
    target = now + timedelta(hours=1)

    start_window = target - timedelta(minutes=5)
    end_window = target + timedelta(minutes=5)

    jobs = Job.objects.filter(
        status=Job.Status.UPCOMING,
        reminder_sent=False
    ).select_related("landscaper", "client")

    for job in jobs:

        job_datetime = datetime.combine(
            job.scheduled_date,
            job.scheduled_time
        )

        job_datetime = timezone.make_aware(
            job_datetime,
            timezone.get_current_timezone()
        )

        if start_window <= job_datetime <= end_window:

            if job.landscaper:

                send_push_notification(
                    user=job.landscaper.user,
                    title="⏰ Job starts in 1 hour",
                    message=f"Job #{job.id} will start soon.",
                    notification_type="job",
                    data={"job_id": job.id}
                )

                job.reminder_sent = True
                job.save(update_fields=["reminder_sent"])