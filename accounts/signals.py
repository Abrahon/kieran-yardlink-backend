from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from profiles.models import AdminProfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserPhone

User = get_user_model()


@receiver(post_save, sender=User)
def create_admin_profile(sender, instance, created, **kwargs):
    """
    Automatically create AdminProfile when user with role='admin' is created.
    """
    if created and getattr(instance, "role", None) == "admin":
        AdminProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_admin_profile(sender, instance, **kwargs):
    """
    Save AdminProfile whenever User is updated.
    """
    if hasattr(instance, "admin_profile"):
        instance.admin_profile.save()




# CONNECT PHONE MODEL AUTOMATICALLY
@receiver(post_save, sender=User)
def create_user_phone(sender, instance, created, **kwargs):
    if created:
        UserPhone.objects.create(user=instance)
