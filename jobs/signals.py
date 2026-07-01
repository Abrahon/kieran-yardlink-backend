from django.db.models.signals import post_save
from django.dispatch import receiver
from jobs.models import Job
from notifications.services import send_push_notification


@receiver(post_save, sender=Job)
def job_created(sender, instance, created, **kwargs):

    if not created:
        return

    user = None

    # safer access pattern
    if getattr(instance, "client", None) and getattr(instance.client, "user", None):
        user = instance.client.user

    elif getattr(instance, "external_client", None) and getattr(instance.external_client, "user", None):
        user = instance.external_client.user

    if not user:
        return

    try:
        send_push_notification(
            user=user,
            title="New Job Created",
            message=f"Job #{instance.id} has been scheduled",
            notification_type="job",
            data={"job_id": instance.id},
        )
    except Exception:
        # never break job creation because notification failed
        pass