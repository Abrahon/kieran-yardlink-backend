from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
# from landscapers .models import BusinessProfile
#  from landscapers.models import BusinessProfile
from invitations .models import TeamInvitation
from accounts.models import User
from subscriptions.models import Plan
User = get_user_model()

class AdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )

    phone = models.CharField(max_length=15, blank=True, null=True)
    image = CloudinaryField("admin_profile", blank=True, null=True)

    def __str__(self):
        return f"{self.user.name}"



    # profiles/models.py
class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pro_landscaper = models.ForeignKey(
        "landscapers.BusinessProfile",
        on_delete=models.CASCADE,  # 🔹 required
        null=True,
        blank=True
    )
    
    name = models.CharField(max_length=255, default="Worker")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("worker_profile", blank=True, null=True)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.name

        


# profiles/models.py
class LandscaperProfilies(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaperprofilies"
    )
    name = models.CharField(max_length=255, default="Landscaper")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("landscaper_profile", blank=True, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    calendar_sync = models.BooleanField(default=False)
    job_reminder= models.BooleanField(default=False)

# landscapers/models.py
# class BusinessProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="landscaper_profile_extra"  # give a unique reverse name
#     )



# client
class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Client")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("client_profile", blank=True, null=True)
    calendar_sync = models.BooleanField(default=False)

    service_reminder = models.BooleanField(default=False)

    def __str__(self):
        return self.name



