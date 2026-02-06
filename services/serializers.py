
# from rest_framework import serializers
# from .models import Service, ClientServicePreference,ServiceImage


# class ServiceImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceImage
#         fields = ["id", "image", "uploaded_at"]

# # ---------------- Service Serializer ----------------
# class ServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Service
#         fields = ["id", "name", "description", "category", "price", "square_feet", "completed", "is_standard"]
        

# # ---------------- Client Preference Write ----------------
# class ClientServicePreferenceWriteSerializer(serializers.ModelSerializer):
#     services = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Service.objects.all()  # all services, standard or custom
#     )

#     class Meta:
#         model = ClientServicePreference
#         fields = ["services", "frequency", "note"]

#     def create(self, validated_data):
#         services = validated_data.pop("services", [])
#         preference = ClientServicePreference.objects.create(**validated_data)
#         preference.services.set(services)
#         return preference

#     def update(self, instance, validated_data):
#         services = validated_data.pop("services", None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         if services is not None:
#             instance.services.set(services)
#         return instance

# # ---------------- Client Preference Read ----------------
# class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
#     services = ServiceSerializer(many=True)
#     total_price = serializers.SerializerMethodField()

#     class Meta:
#         model = ClientServicePreference
#         fields = ["services", "frequency", "note", "total_price", "updated_at"]

#     def get_total_price(self, obj):
#         return sum([s.price for s in obj.services.all() if s.price])


# class LandscaperServicesSerializer(serializers.Serializer):
#     """
#     Separate services into completed and remaining (next) services
#     """
#     completed_services = ServiceSerializer(many=True)
#     next_services = ServiceSerializer(many=True)

# serializers.py
# from rest_framework import serializers
# from .models import Service, ClientServicePreference, ServiceSchedule
# from property.models import Property
from rest_framework import serializers
from .models import (
    ClientService,
    ClientServicePreference,
    ServiceSchedule,
    ScheduleCompletionImage
)


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientService
        fields = [
            "id",
            "name",
            "description",
            "category",
            "price",
            "square_feet",
            "is_standard",
            "image"
        ]
    def get_property_size(self, obj):

        client_profile = self.context.get("client_profile")
        if not client_profile:
            return None

        property_obj = Property.objects.filter(
            owner=client_profile
        ).only("property_size").first()

        return property_obj.property_size if property_obj else None



class ClientServicePreferenceWriteSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ClientService.objects.all()
    )

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note"]


class ClientServicePreferenceReadSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = ClientServicePreference
        fields = ["services", "frequency", "note", "total_price"]

    def get_total_price(self, obj):
        return sum([s.price or 0 for s in obj.services.all()])


class ScheduleCompletionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleCompletionImage
        fields = ["id", "image", "uploaded_at"]


class ServiceScheduleSerializer(serializers.ModelSerializer):
    service = ServiceSerializer()
    images = ScheduleCompletionImageSerializer(many=True)

    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "service",
            "scheduled_date",
            "scheduled_time",
            "is_completed",
            "completed_at",
            "images"
        ]

        
from rest_framework import serializers
from .models import ServiceSchedule

class ScheduleRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = ["scheduled_date", "scheduled_time"]

    def validate(self, attrs):
        instance = self.instance
        if instance.is_completed:
            raise serializers.ValidationError("Completed job cannot be rescheduled")
        return attrs




class ServiceMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientService
        fields = ["id", "name", "price", "category"]

class ServiceOverviewSerializer(serializers.Serializer):
    frequency = serializers.CharField()
    property_size = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    last_service_date = serializers.DateField(allow_null=True)
    next_service_date = serializers.DateField(allow_null=True)
    next_payment_date = serializers.DateField(allow_null=True)
    services = ServiceMiniSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    property_active = serializers.SerializerMethodField()

    def get_property_size(self, obj):
        client_profile = self.context.get("client_profile")
        if not client_profile:
            return None

        property_obj = Property.objects.filter(owner=client_profile.user).order_by("-created_at").first()
        return property_obj.property_size if property_obj else None

    def get_property_image(self, obj):
        client_profile = self.context.get("client_profile")
        if not client_profile:
            return None

        property_obj = Property.objects.filter(owner=client_profile.user).order_by("-created_at").first()
        if not property_obj or not property_obj.images:
            return None

        # images is a list of URLs
        if isinstance(property_obj.images, list) and property_obj.images:
            return property_obj.images[0]

        return None

    def get_total_price(self, obj):
        services = obj.get("services", [])
        total = sum(float(service.price) for service in services if service.price)
        return total

    def get_property_active(self, obj):
        """
        Returns True if this property is the latest property of the client.
        """
        client_profile = self.context.get("client_profile")
        if not client_profile:
            return False

        latest_property = Property.objects.filter(owner=client_profile.user).order_by("-created_at").first()
        if not latest_property:
            return False

        # You can optionally check if obj has a property reference
        property_in_obj = obj.get("property_id")
        if property_in_obj:
            return latest_property.id == property_in_obj

        # Default to True for the latest property
        return True
