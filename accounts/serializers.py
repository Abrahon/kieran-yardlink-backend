
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator
from .utils import generate_otp, send_otp_email
from django.utils import timezone

User = get_user_model() 
# ---------------------------
# SIGNUP SERIALIZER
# ---------------------------
from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User, RoleChoices,OTP,UserReport  # make sure RoleChoices exists
import re

from .enums import RoleChoices


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z\s]+$",
                message="Name can only contain letters and spaces.",
            )
        ],
        error_messages={
            "blank": "Name field is required.",
            "required": "Please provide your name.",
        },
    )

    email = serializers.EmailField(
        error_messages={
            "invalid": "Enter a valid email address.",
            "required": "Email field is required.",
            "blank": "Email cannot be empty."
        }
    )

    phone = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^[0-9]{10,15}$",
                message="Phone number must contain 10–15 digits.",
            )
        ],
        error_messages={
            "required": "Phone number is required.",
            "blank": "Phone number cannot be empty.",
        }
    )

    address = serializers.CharField(
        error_messages={
            "required": "Address field is required.",
            "blank": "Address cannot be empty."
        }
    )

    latitude = serializers.DecimalField(
        max_digits=20,
        decimal_places=18,
        required=False,
        allow_null=True
    )

    longitude = serializers.DecimalField(
        max_digits=20,
        decimal_places=18,
        required=False,
        allow_null=True
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "Password must be at least 8 characters long.",
            "blank": "Password field cannot be empty.",
        },
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "Confirm password must be at least 8 characters long.",
            "blank": "Confirm password field cannot be empty.",
        },
    )

    role = serializers.ChoiceField(
        choices=RoleChoices.choices,
        error_messages={
            "required": "Role field is required.",
            "invalid_choice": "Invalid role. Choose a valid role."
        }
    )
    
    allow_notification = serializers.BooleanField(
        required=False,
        default=False
    )

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise serializers.ValidationError("This email is already registered.")

        return email

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs





class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")

        if not re.match(r"^\+?[0-9]{10,15}$", value):
            raise serializers.ValidationError("Phone format invalid")

        return value


# ---------------------------
# LOGIN SERIALIZER
# ---------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        attrs["user"] = user
        return attrs



class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def create(self, validated_data):
        # 1️⃣ Get the user
        user = User.objects.get(email=validated_data["email"])

        # 2️⃣ Generate OTP
        code = generate_otp()
        OTP.objects.create(user=user, code=code)

        # 3️⃣ Send OTP via email
        send_otp_email(user.email, code, name=user.name)

        # 4️⃣ Return the user object (not a dict) so the view can access user.email
        return user




# Resend otp
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Optional: block if already verified
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("This account is already verified.")
        return value

# ---------------------------
# VERIFY OTP SERIALIZER
# ---------------------------


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp')

        # check OTP exists
        try:
            otp = OTP.objects.filter(email=email).latest('created_at')
        except OTP.DoesNotExist:
            raise serializers.ValidationError("OTP not found for this email.")

        if otp.is_expired():
            raise serializers.ValidationError("OTP expired.")

        if otp.code != otp_code:
            raise serializers.ValidationError("Invalid OTP.")

        data['otp_instance'] = otp
        return data

# ---------------------------
# VERIFY OTP SERIALIZER forget password
# ---------------------------
class VerifyOTPForgetSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        request = self.context.get("request")
        email = request.data.get("email")

        if not email:
            raise serializers.ValidationError(
                "No OTP request found. Please request OTP first."
            )

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User not found.")

        otp = OTP.objects.filter(user=user, code=data["code"]).order_by("-created_at").first()
        if not otp or otp.is_expired():
            raise serializers.ValidationError("OTP is invalid or expired.")

        data["user"] = user
        return data

# ---------------------------
# RESET PASSWORD SERIALIZER
# ---------------------------
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        user = self.context.get("user")
        if not user:
            raise serializers.ValidationError("OTP verification required.")
        self.user = user
        return attrs

    def save(self, **kwargs):
        self.user.set_password(self.validated_data["new_password"])
        self.user.save()
        OTP.objects.filter(user=self.user).delete()
        return self.user


# ---------------------------
# CHANGE PASSWORD SERIALIZER
# ---------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old password is incorrect.")
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user

        



from django.utils import timezone
from datetime import timedelta
class UserSerializer(serializers.ModelSerializer):
    landscaper_plan = serializers.SerializerMethodField()
    plan_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "address",
            "phone",
            "role",
            "is_active",
            "date_joined",
            "landscaper_plan",
            "plan_type",
        ]

    def get_landscaper_plan(self, obj):
        # use field first
        if obj.landscaper_plan:
            return obj.landscaper_plan

        # fallback to active subscription
        subscription = (
            obj.subscription_set
            .filter(is_active=True, status__in=["active", "trialing"])
            .select_related("plan")
            .first()
        )
        return subscription.plan.name if subscription else None

    def get_plan_type(self, obj):
        if obj.plan_type:
            return obj.plan_type

        subscription = (
            obj.subscription_set
            .filter(is_active=True, status__in=["active", "trialing"])
            .first()
        )
        if not subscription:
            return None
        return "free_trial" if subscription.is_trial else "paid"





# accounts/serializers.py



# serializers.py

from rest_framework import serializers
from .models import UserReport

class UserReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserReport
        fields = ["note"]

# admin serializers

from rest_framework import serializers
from .models import User


class AdminUserDetailSerializer(serializers.ModelSerializer):
    subscription = serializers.DictField(read_only=True)
    business_profile = serializers.DictField(read_only=True)
    recent_jobs = serializers.ListField(read_only=True)

    total_revenue = serializers.FloatField(read_only=True)
    total_jobs = serializers.IntegerField(read_only=True)
    completed_jobs = serializers.IntegerField(read_only=True)
    pending_jobs = serializers.IntegerField(read_only=True)
    total_clients = serializers.IntegerField(read_only=True)
    total_landscapers = serializers.IntegerField(read_only=True)

    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
        #  NAME OVERRIDE
    name = serializers.SerializerMethodField()

    # =========================
    #  ADD THIS (PLAN INFO)
    # =========================
    plan_type = serializers.CharField(source="current_plan_type", read_only=True)
    plan_expiry = serializers.DateTimeField(source="current_plan_expiry", read_only=True)

    # ✅ OVERRIDE NAME HERE
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name", 
            "email",
            "phone",
            "address",
            "role",
            "is_active",
            "is_flagged",
            "admin_notes",
            "date_joined",
            "last_login",

            "subscription",
            "business_profile",
            "plan_type",        # ✅ ADD HERE
            "plan_expiry",  

            "total_revenue",
            "total_jobs",
            "completed_jobs",
            "pending_jobs",
            "total_clients",
            "total_landscapers",
            "average_rating",
            "review_count",

            "recent_jobs",
        ]

    # ✅ REAL NAME LOGIC
    def get_name(self, obj):
        # 1. If Django user full name exists
        full_name = obj.get_full_name()
        if full_name:
            return full_name

        # 2. First + last name fallback
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()

        # 3. If landscaper profile exists (FIX RELATION NAME)
        landscaper_profile = getattr(obj, "landscaper_profile", None)
        if landscaper_profile and getattr(landscaper_profile, "name", None):
            return landscaper_profile.name

        # 4. Final fallback (NEVER role)
        return obj.email

    def get_average_rating(self, obj):
        if obj.role != "landscaper":
            return 0.0
        return round(float(getattr(obj, "average_rating", 0.0) or 0.0), 2)

    def get_review_count(self, obj):
        if obj.role != "landscaper":
            return 0
        return int(getattr(obj, "review_count", 0) or 0)

    def get_last_login(self, obj):
        return obj.last_login
    


class AdminUserUpdateSerializer(serializers.Serializer):

    action = serializers.ChoiceField(
        choices=["pause", "unpause", "flag", "unflag"],
        required=False
    )

    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    role = serializers.CharField(required=False)


# admin user serializers
# accounts/serializers.py

class AdminUserSerializer(serializers.ModelSerializer):
    landscaper_plan = serializers.SerializerMethodField()
    plan_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "role",
            "is_active",
            "is_flagged",
            "admin_notes",
            "date_joined",
            "last_login",
            "landscaper_plan",
            "plan_type",
        ]

    def get_landscaper_plan(self, obj):
        if obj.landscaper_plan:
            return obj.landscaper_plan

        subscription = (
            obj.subscription_set
            .filter(is_active=True, status__in=["active", "trialing"])
            .select_related("plan")
            .first()
        )
        return subscription.plan.name if subscription else None

    def get_plan_type(self, obj):
        if obj.plan_type:
            return obj.plan_type

        subscription = (
            obj.subscription_set
            .filter(is_active=True, status__in=["active", "trialing"])
            .first()
        )

        if not subscription:
            return None

        return "free_trial" if subscription.is_trial else "paid"