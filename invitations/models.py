# invitations/models.py
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from landscapers.models import BusinessProfile


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    EXPIRED = "expired", "Expired"


class TeamInvitation(models.Model):
    inviter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_invitations"
    )

    landscaper = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="team_invitations"
    )

    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )

    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at


# class BusinessEmployee(models.Model):
#     landscaper = models.ForeignKey(
#         "LandscaperProfile",
#         on_delete=models.CASCADE,
#         related_name="employees"
#     )

#     user = models.ForeignKey(
#         "accounts.User",
#         on_delete=models.CASCADE
#     )

#     is_active = models.BooleanField(default=True)
#     joined_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ("landscaper", "user")

#     def __str__(self):
#         return f"{self.user.email} - {self.landscaper.business_name}"

# class EmployeePermission(models.Model):
#     employee = models.OneToOneField(
#         BusinessEmployee,
#         on_delete=models.CASCADE,
#         related_name="permissions"
#     )

#     can_access_calendar = models.BooleanField(default=True)
#     can_manage_services = models.BooleanField(default=False)
#     can_manage_business_profile = models.BooleanField(default=False)
#     can_access_messages = models.BooleanField(default=True)

#     def __str__(self):
#         return f"Permissions - {self.employee.user.email}"