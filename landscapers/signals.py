# landscapers/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from landscapers.models import LandscaperProfile
from qr.models import LandscaperQRCode


@receiver(post_save, sender=LandscaperProfile)
def create_qr_code(sender, instance, created, **kwargs):
    if created:
        LandscaperQRCode.objects.create(landscaper=instance)
