# from decimal import Decimal
# from rest_framework import serializers

# from .models import Service, ClientServicePreference
# from subscriptions.models import Subscription

# class ServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Service
#         fields = [
#             "id",
#             "name",
#             "description",
#             "category",
#             # "is_addon",
#             "price",
#             "square_feet",
#             "created_at",
#         ]
#         read_only_fields = ["id", "created_at"]

#     def validate(self, attrs):
#         user = self.context["request"].user
#         subscription = Subscription.objects.filter(user=user, status="active").first()
#         plan_name = subscription.plan.name.lower() if subscription else "basic"

#         # Prevent Basic users from setting price/square_feet
#         if not plan_name.startswith("pro"):
#             if attrs.get("price") is not None or attrs.get("square_feet") is not None:
#                 raise serializers.ValidationError(
#                     "Only Pro subscription users can set price and square feet."
#                 )

#         return attrs


    
#     def create(self, validated_data):
#         user = self.context["request"].user
#         # Access landscaper profile via related_name
#         profile = getattr(user, "landscaper_profile", None)
#         if not profile:
#             raise serializers.ValidationError("Landscaper profile not found for this user.")
#         return Service.objects.create(landscaper=profile, **validated_data)


#     def update(self, instance, validated_data):
#         user = self.context["request"].user
#         subscription = Subscription.objects.filter(user=user, status="active").first()
#         plan_name = subscription.plan.name.lower() if subscription else "basic"

#         # Prevent Basic users from updating price/square_feet
#         if not plan_name.startswith("pro"):
#             validated_data.pop("price", None)
#             validated_data.pop("square_feet", None)

#         return super().update(instance, validated_data)


# # clinet serializers

# class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
#     services = ServiceReadSerializer(many=True, read_only=True)
#     total_price = serializers.SerializerMethodField()

#     class Meta:
#         model = ClientServicePreference
#         fields = [
#             "services",
#             "frequency",
#             "note",
#             "total_price",
#             "updated_at",
#         ]

#     def get_total_price(self, obj):
#         total = Decimal("0.00")
#         for service in obj.services.all():
#             if service.price:
#                 total += service.price
#         return total

from decimal import Decimal
from rest_framework import serializers
from .models import Service, ClientServicePreference
from subscriptions.models import Subscription


# ----------------------------
# Read-only serializer for nested use
# ----------------------------
# class ServiceReadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Service
#         fields = [
#             "id",
#             "name",
#             "description",
#             "category",
#             "price",
#             "square_feet",
#             "created_at",
#         ]
#         read_only_fields = fields


# # ----------------------------
# # Main Service Serializer
# # ----------------------------
# class ServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Service
#         fields = [
#             "id",
#             "name",
#             "description",
#             "category",
#             "price",
#             "square_feet",
#             "created_at",
#         ]
#         read_only_fields = ["id", "created_at"]

#     def validate(self, attrs):
#         user = self.context["request"].user
#         subscription = Subscription.objects.filter(user=user, status="active").first()
#         plan_name = subscription.plan.name.lower() if subscription else "basic"

#         if not plan_name.startswith("pro"):
#             if attrs.get("price") is not None or attrs.get("square_feet") is not None:
#                 raise serializers.ValidationError(
#                     "Only Pro subscription users can set price and square feet."
#                 )

#         return attrs

#     def create(self, validated_data):
#         user = self.context["request"].user
#         profile = getattr(user, "landscaper_profile", None)
#         if not profile:
#             raise serializers.ValidationError("Landscaper profile not found for this user.")
#         return Service.objects.create(landscaper=profile, **validated_data)

#     def update(self, instance, validated_data):
#         user = self.context["request"].user
#         subscription = Subscription.objects.filter(user=user, status="active").first()
#         plan_name = subscription.plan.name.lower() if subscription else "basic"

#         if not plan_name.startswith("pro"):
#             validated_data.pop("price", None)
#             validated_data.pop("square_feet", None)

#         return super().update(instance, validated_data)


# # ----------------------------
# # Client Service Preference Serializer
# # ----------------------------


# class ClientServicePreferenceSerializer(serializers.ModelSerializer):
#     services = serializers.PrimaryKeyRelatedField(
#         queryset=Service.objects.all(),
#         many=True,
#         required=False
#     )
#     total_price = serializers.SerializerMethodField()  # Add total_price

#     class Meta:
#         model = ClientServicePreference
#         fields = [
#             "services",
#             "frequency",
#             "note",
#             "total_price",  # include here
#             "updated_at",
#         ]
#         read_only_fields = ["updated_at", "total_price"]  # total_price is read-only

#     def get_total_price(self, obj):
#         total = Decimal("0.00")
#         for service in obj.services.all():
#             if service.price:
#                 total += service.price
#         return total

#     def update(self, instance, validated_data):
#         services = validated_data.pop("services", None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if services is not None:
#             instance.services.set(services)
#         return instance

from rest_framework import serializers
from .models import Service, ClientServicePreference
from decimal import Decimal

# ---------------- Service Serializer ----------------
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id", "name", "description", "category",
            "price", "square_feet", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

# ---------------- Client Service Preference Serializer (write) ----------------
class ClientServicePreferenceSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note", "updated_at"]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if services is not None:
            instance.services.set(services)
        return instance

# ---------------- Client Service Preference Read Serializer ----------------
class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note", "total_price", "updated_at"]

    def get_total_price(self, obj):
        total = Decimal("0.00")
        for service in obj.services.all():
            if service.price:
                total += service.price
        return total
