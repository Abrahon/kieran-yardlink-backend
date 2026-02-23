from rest_framework import serializers
from .models import Plan,Subscription
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

from decimal import Decimal


class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "description",
            "price",
            "discount",
            "duration",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "is_active","created_at", "updated_at")

    # Validate discount
    def validate_discount(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Discount must be between 0 and 100."
            )
        return value

    # Add computed field in response
    def to_representation(self, instance):
        data = super().to_representation(instance)

        price = instance.price        # Decimal
        discount = instance.discount  # Decimal

        final_price = price - (price * discount / Decimal("100"))

        data["final_price"] = float(final_price)
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)  
    remaining_days = serializers.SerializerMethodField()
    is_trial = serializers.SerializerMethodField() 
    trial_remaining_days = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()  # override status dynamically
    is_active = serializers.SerializerMethodField()  # override is_active dynamically

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user",
            "user_name",     
            "user_email",
            "plan",
            "plan_name",
            "status",
            "is_active",
            "is_trial",
            "trial_remaining_days", 
            "start_date",
            "end_date",
            "remaining_days",
            "created_at",
        ]
        read_only_fields = (
            "id",
            "user",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "user_name",
            "user_email",
            "plan_name",
            "is_trial",
        )


    def get_remaining_days(self, obj):
        remaining = (obj.end_date - timezone.now()).days
        return max(remaining, 0)
    
    def get_is_trial(self, obj):
        trial_period_days = 14
        trial_end_date = obj.start_date + timedelta(days=trial_period_days)
        return timezone.now() <= trial_end_date
    
    # def get_is_trial(self, obj):
    #     trial_days = 14
    #     trial_end = obj.start_date + timedelta(days=trial_days)
    #     return timezone.now() <= trial_end

    # def get_remaining_days(self, obj):
    #     now = timezone.now()
    #     remaining = (obj.end_date - now).days
    #     return max(remaining, 0)

    def get_trial_remaining_days(self, obj):
        trial_days = 14
        trial_end = obj.start_date + timedelta(days=trial_days)
        now = timezone.now()
        if now <= trial_end:
            return max((trial_end - now).days, 0)
        return None  # not a trial anymore

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user
        plan = attrs.get("plan")

        if user is None:
            raise serializers.ValidationError({"user": "User must be authenticated."})

        # Role validation
        if user.role not in ["client", "landscaper"]:
            raise serializers.ValidationError(
                {"user": "Only clients or landscapers can subscribe."}
            )

        # Plan active
        if not plan.is_active:
            raise serializers.ValidationError({"plan": "This plan is inactive."})

        # One active subscription per user
        if Subscription.objects.filter(user=user, status="active").exists():
            raise serializers.ValidationError(
                {"subscription": "User already has an active subscription."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        plan = validated_data["plan"]

        start_date = timezone.now()
        duration_days = 30 if plan.duration == "monthly" else 365
        end_date = start_date + timedelta(days=duration_days)

        # Double-check before creating
        if Subscription.objects.filter(user=user, status="active").exists():
            raise serializers.ValidationError(
                {"subscription": "User already has an active subscription."}
            )
    def get_status(self, obj):
        if not obj.is_trial and obj.end_date < timezone.now():
            return "expired"  # Paid subscription expired
        return obj.status

    # -----------------------------
    # Dynamic is_active
    # -----------------------------
    def get_is_active(self, obj):
        if not obj.is_trial and obj.end_date < timezone.now():
            return False  # Paid subscription expired
        return obj.is_active


        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            status="active",
            is_active=True,        
            start_date=start_date,
            end_date=end_date,
        )



class SubscriptionUpgradeSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_price = serializers.DecimalField(source="plan.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "user", "plan_name", "plan_price", "start_date", "end_date", "status", "auto_renew"]

# admin subscriptions 
from rest_framework import serializers
from .models import Subscription
from django.utils import timezone

class AdminSubscriptionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_price = serializers.DecimalField(
        source="plan.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "user_email",
            "user_role",
            "plan_name",
            "plan_price",
            "status",
            "start_date",
            "end_date",
            "is_expired",
            "created_at",
        ]

    def get_is_expired(self, obj):
        return obj.end_date < timezone.now()
