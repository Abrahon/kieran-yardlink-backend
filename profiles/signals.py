from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings
from .models import AdminProfile

User = apps.get_model(settings.AUTH_USER_MODEL)

@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    if created:
        AdminProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_admin_profile(sender, instance, **kwargs):
    # Use the correct related name from AdminProfile
    try:
        instance.admin_profile.save()
    except AdminProfile.DoesNotExist:
        pass
