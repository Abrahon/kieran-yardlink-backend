from rest_framework import serializers
from .models import Service
from subscriptions.models import Subscription
from rest_framework import serializers
from .models import ClientServicePreference
from services.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "category",
            # "is_addon",
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
        # Access landscaper profile via related_name
        profile = getattr(user, "landscaper_profile", None)
        if not profile:
            raise serializers.ValidationError("Landscaper profile not found for this user.")
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


# clinet serializers



class ClientServicePreferenceSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = ClientServicePreference
        fields = [
            "services",
            "frequency",
            "note",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if services is not None:
            instance.services.set(services)

        return instance
