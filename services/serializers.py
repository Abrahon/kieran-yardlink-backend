from .models import AddOnService
from rest_framework import serializers
from .models import (
    ClientService,
    ClientServicePreference,
    ServiceSchedule,
    ScheduleCompletionImage
)
from rest_framework import serializers
from .models import ServiceSchedule, ScheduleCompletionImage, ClientService
from rest_framework import serializers
from .models import ServiceSchedule
from property.models import Property

from rest_framework import serializers
from services.models import ServiceSchedule, ClientService, ScheduleCompletionImage



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



class CompletedServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientService
        fields = ["id", "name", "price"]




from rest_framework import serializers
from .models import AddOnService
from django.contrib.auth import get_user_model

User = get_user_model()

class AddOnServiceSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()  # show client info

    class Meta:
        model = AddOnService
        fields = ["id", "name", "price", "client", "created_at", "updated_at"]

    def get_client(self, obj):
        # You can return id only, or a dict with id & name/email
        return {
            "id": obj.client.id,
            "name": obj.client.get_full_name() or obj.client.username,
            "email": obj.client.email
        }


class ServiceScheduleSerializer(serializers.ModelSerializer):
    completed_services = CompletedServiceSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    before_images = serializers.SerializerMethodField()
    after_images = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    add_ons = AddOnServiceSerializer(many=True, read_only=True)
    add_on_ids = serializers.PrimaryKeyRelatedField(
        queryset=AddOnService.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "scheduled_date",
            "scheduled_time",
            "is_completed",
            "completed_at",
            "completion_note",
            "completed_services",
            "total_price",
            "add_ons",
            "add_on_ids",
            "payment_status",
            "before_images",
            "after_images",
            "images"
        ]

    def get_before_images(self, obj):
        return [img.image.url for img in obj.images.filter(image_type="before")]

    def get_after_images(self, obj):
        return [img.image.url for img in obj.images.filter(image_type="after")]

    def get_images(self, obj):
        # Return all images (both before and after)
        return [img.image.url for img in obj.images.all()]

    def get_total_price(self, obj):
        completed_services = obj.completed_services.all()
        if completed_services.exists():
            return sum(s.price for s in completed_services)
        return obj.service.price

    def get_payment_status(self, obj):
        return obj.get_payment_status_display()

    # def get_total_price(self, obj):
    #     base_price = obj.service.price if obj.service else 0
    #     add_on_total = obj.add_ons.aggregate(total=models.Sum("price"))["total"] or 0
    #     return base_price + add_on_total

    def update(self, instance, validated_data):
        add_on_ids = validated_data.pop("add_on_ids", None)
        instance = super().update(instance, validated_data)
        if add_on_ids is not None:
            instance.add_ons.set(add_on_ids)
        return instance


        
# rechedule serializers
class ScheduleRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = ["scheduled_date", "scheduled_time"]

    def validate(self, attrs):
        instance = self.instance
        if instance.is_completed:
            raise serializers.ValidationError("Completed job cannot be rescheduled")
        return attrs


# services/serializers.py


class AddOnServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOnService
        fields = ["id", "name", "price", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

# service mini serializers
class ServiceMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientService
        fields = ["id", "name", "price", "category"]


# service overview
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


