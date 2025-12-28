from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class RainAlertSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE
    )
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
