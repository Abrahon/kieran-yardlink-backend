

# # from decimal import Decimal
# # from rest_framework import serializers
# # from .models import Service, ClientServicePreference
# # from subscriptions.models import Subscription


# # from rest_framework import serializers
# # from .models import Service, ClientServicePreference
# # from decimal import Decimal

# # # ---------------- Service Serializer ----------------
# # class ServiceSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Service
# #         fields = [
# #             "id", "name", "description", "category",
# #             "price", "square_feet", "created_at"
# #         ]
# #         read_only_fields = ["id", "created_at"]

# # # ---------------- Client Service Preference Serializer (write) ----------------
# # class ClientServicePreferenceSerializer(serializers.ModelSerializer):
# #     services = serializers.PrimaryKeyRelatedField(
# #         queryset=Service.objects.all(),
# #         many=True,
# #         required=False
# #     )

# #     class Meta:
# #         model = ClientServicePreference
# #         fields = ["services", "frequency", "note", "updated_at"]
# #         read_only_fields = ["updated_at"]

# #     def update(self, instance, validated_data):
# #         services = validated_data.pop("services", None)
# #         for attr, value in validated_data.items():
# #             setattr(instance, attr, value)
# #         instance.save()
# #         if services is not None:
# #             instance.services.set(services)
# #         return instance

# # # ---------------- Client Service Preference Read Serializer ----------------
# # class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
# #     services = ServiceSerializer(many=True, read_only=True)
# #     total_price = serializers.SerializerMethodField()

# #     class Meta:
# #         model = ClientServicePreference
# #         fields = ["services", "frequency", "note", "total_price", "updated_at"]

# #     def get_total_price(self, obj):
# #         total = Decimal("0.00")
# #         for service in obj.services.all():
# #             if service.price:
# #                 total += service.price
# #         return total
# from decimal import Decimal
# from rest_framework import serializers
# from .models import Service, ClientServicePreference


# # ---------------- Service ----------------
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
#         ]


# # ---------------- Client Preference (WRITE) ----------------
# class ClientServicePreferenceWriteSerializer(serializers.ModelSerializer):
#     services = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Service.objects.none()  # IMPORTANT
#     )

#     class Meta:
#         model = ClientServicePreference
#         fields = ["services", "frequency", "note"]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         request = self.context.get("request")
#         if request and request.user.is_authenticated:
#             # Example: allow only services from assigned landscaper
#             self.fields["services"].queryset = Service.objects.all()


# # ---------------- Client Preference (READ) ----------------
# class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
#     services = ServiceSerializer(many=True)
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
from rest_framework import serializers
from .models import Service, ClientServicePreference

# ---------------- Service Serializer ----------------
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description", "category", "price", "square_feet", "is_standard"]

# ---------------- Client Preference Write ----------------
class ClientServicePreferenceWriteSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Service.objects.all()  # all services, standard or custom
    )

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note"]

    def create(self, validated_data):
        services = validated_data.pop("services", [])
        preference = ClientServicePreference.objects.create(**validated_data)
        preference.services.set(services)
        return preference

    def update(self, instance, validated_data):
        services = validated_data.pop("services", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if services is not None:
            instance.services.set(services)
        return instance

# ---------------- Client Preference Read ----------------
class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note", "total_price", "updated_at"]

    def get_total_price(self, obj):
        return sum([s.price for s in obj.services.all() if s.price])
