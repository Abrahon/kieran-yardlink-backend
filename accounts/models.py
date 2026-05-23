# accounts/models.py
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from .enums import RoleChoices

from django.db import models
from django.utils import timezone
from datetime import timedelta
import random



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        """
        Create and save a regular user. Role is required (no default).
        """
        if not email:
            raise ValueError("Users must have an email address")
        if role is None:
            raise ValueError("A role must be provided when creating a user")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        # ensure staff/superuser flags are consistent with role
        if role == RoleChoices.ADMIN:
            user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser. Force admin role + flags.
        """
        extra_fields.setdefault('role', RoleChoices.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True)

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=18, blank=True, null=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=18, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    is_flagged = models.BooleanField(default=False)
    allow_notification = models.BooleanField(default=False)

  

    # NOTE: no default role. Must be provided.
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    # Plan info 
    landscaper_plan = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Pro"
    plan_type = models.CharField(max_length=20, blank=True, null=True)  

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)   
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_permissions_set',
        blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    # include 'role' in REQUIRED_FIELDS so createsuperuser prompts for it if needed
    REQUIRED_FIELDS = ['name', 'role']

    def __str__(self):
        return self.email

    def clean(self):
        # optional: ensure role is one of choices
        super().clean()
        if self.role not in RoleChoices.values:
            raise ValueError("Invalid role for user")
     #  Add this method:
    def get_full_name(self):
        """
        Return the full name of the user for compatibility with Django conventions.
        """
        return self.name or self.email


# SMS verification model
class UserPhone(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=20, unique=True)

    is_verified = models.BooleanField(default=False)
    sms_opt_in = models.BooleanField(default=False)

    verification_code = models.CharField(max_length=6, null=True, blank=True)
    code_created_at = models.DateTimeField(null=True, blank=True)

    verified_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        otp = str(random.randint(100000, 999999))
        self.verification_code = otp
        self.code_created_at = timezone.now()
        self.save()
        return otp

    def is_otp_expired(self):
        if not self.code_created_at:
            return True
        return timezone.now() > self.code_created_at + timedelta(minutes=5)



class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        if self.user:
            return f"{self.code} ({self.user.email})"
        return f"{self.code} ({self.email})"   



# report model


from django.conf import settings

class UserReport(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_made"
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_received"
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.email} against {self.reported_user.email}"


# create audit model
class AdminAuditLog(models.Model):

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_actions"
    )

    action = models.CharField(max_length=255)

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affected_actions"
    )

    details = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.email} - {self.action}"
    

# login activity
from django.db import models
from django.conf import settings

class LoginActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_activities"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    # optional (nice for dashboards)
    device_type = models.CharField(max_length=50, blank=True, null=True)   # "mobile", "desktop", "tablet"
    os = models.CharField(max_length=50, blank=True, null=True)           # "Android", "iOS", "Windows"
    browser = models.CharField(max_length=50, blank=True, null=True)      # "Chrome", "Safari"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.ip_address} - {self.created_at}"

