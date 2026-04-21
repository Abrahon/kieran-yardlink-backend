
from rest_framework import serializers
from .models import (
    ClientService,
    ClientServicePreference
)
from rest_framework import serializers
from rest_framework import serializers
from property.models import Property

from rest_framework import serializers
from services.models import  ClientService



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





class CompletedServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientService
        fields = ["id", "name", "price"]





# service overview
class ServiceOverviewSerializer(serializers.Serializer):
    frequency = serializers.CharField()
    property_size = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    last_service_date = serializers.DateField(allow_null=True)
    next_service_date = serializers.DateField(allow_null=True)
    next_payment_date = serializers.DateField(allow_null=True)
    # services = ServiceMiniSerializer(many=True)
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


