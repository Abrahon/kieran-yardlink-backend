from rest_framework import serializers
from .models import Service
from subscriptions.models import Subscription

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "category",
            "is_addon",
            "price",
            "square_feet",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        subscription = Subscription.objects.filter(user=user, status="active").first()
        plan_name = subscription.plan.name.lower() if subscription else "basic"

        # Prevent Basic users from setting price/square_feet
        if not plan_name.startswith("pro"):
            if attrs.get("price") is not None or attrs.get("square_feet") is not None:
                raise serializers.ValidationError(
                    "Only Pro subscription users can set price and square feet."
                )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        profile = user.landscaper_profile
        return Service.objects.create(landscaper=profile, **validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        subscription = Subscription.objects.filter(user=user, status="active").first()
        plan_name = subscription.plan.name.lower() if subscription else "basic"

        # Prevent Basic users from updating price/square_feet
        if not plan_name.startswith("pro"):
            validated_data.pop("price", None)
            validated_data.pop("square_feet", None)

        return super().update(instance, validated_data)
