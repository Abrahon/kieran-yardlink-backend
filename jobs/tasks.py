from django.utils import timezone
from datetime import datetime
from celery import shared_task
from jobs.models import Job


@shared_task
def update_expired_jobs():

    now = timezone.now()

    jobs = Job.objects.filter(
        status=Job.Status.UPCOMING,
        scheduled_date__isnull=False,
        scheduled_time__isnull=False
    )

    for job in jobs:

        # combine date + time
        job_dt = datetime.combine(job.scheduled_date, job.scheduled_time)

        # ✅ make it timezone-safe (IMPORTANT FIX)
        job_dt = timezone.make_aware(job_dt, is_dst=None)

        # convert BOTH to same timezone
        job_dt = job_dt.astimezone(timezone.utc)

        if job_dt < now:
            job.status = Job.Status.MISSED
            job.save(update_fields=["status"])