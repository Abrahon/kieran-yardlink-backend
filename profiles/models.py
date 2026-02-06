from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from landscapers .models import LandscaperProfile
from invitations .models import TeamInvitation
from accounts.models import User
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
        
        LandscaperProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    

    name = models.CharField(max_length=255, default="Worker")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("worker_profile", blank=True, null=True)
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.name

        
# landscaper 


# profiles/models.py
# class LandscaperProfilies(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="landscaper_profile")
#     name = models.CharField(max_length=255, default="Landscaper")
#     phone = models.CharField(max_length=20, blank=True, default="")
#     image = CloudinaryField("landscaper_profile", blank=True, null=True)
#     stripe_account_id = models.CharField(max_length=255, blank=True, null=True) 


#     def __str__(self):
#         return self.name


# profiles/models.py
class LandscaperProfilies(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaperprofilies"  # explicitly name the reverse accessor
    )
    name = models.CharField(max_length=255, default="Landscaper")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("landscaper_profile", blank=True, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)

# landscapers/models.py
class LandscaperProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="landscaper_profile_extra"  # give a unique reverse name
    )





# client
class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Client")
    phone = models.CharField(max_length=20, blank=True, default="")
    image = CloudinaryField("client_profile", blank=True, null=True)

    def __str__(self):
        return self.name



