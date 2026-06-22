from django.db.models.signals import post_save
from django.dispatch import receiver
from jobs.models import Job
from notifications.services import send_push_notification


@receiver(post_save, sender=Job)
def job_created(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.client:
        user = instance.client.user
    elif instance.external_client:
        user = instance.external_client.user
    else:
        return

    send_push_notification(
        user=user,
        title="New Job Created",
        message=f"Job #{instance.id} has been scheduled",
        notification_type="job",
        data={"job_id": instance.id}
    )