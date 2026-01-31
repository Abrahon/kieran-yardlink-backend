


from rest_framework import serializers
from django.db import transaction
from .models import LandscaperProfile
from services.models import Service
from services.serializers import ServiceSerializer

from .models import Service
import json

from rest_framework import serializers
from .models import LandscaperProfile

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LandscaperProfile
#         fields = [
#             "business_name",
#             "business_email",
#             "business_phone",
#             "latitude",
#             "longitude",
#             "profile",  # this will automatically give the Cloudinary URL
#         ]
#     def get_profile(self, obj):
#         """Return Cloudinary URL"""
#         if obj.image:
#             return obj.profile.url
#         return None
from rest_framework import serializers
from .models import LandscaperProfile
from rest_framework import serializers
from .models import LandscaperProfile

from rest_framework import serializers
from .models import LandscaperProfile

# serializers.py
class BusinessLandscaperProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)  # make writable

    class Meta:
        model = LandscaperProfile
        fields = [
            "business_name",
            "business_email",
            "business_phone",
            "latitude",
            "longitude",
            "profile_image",
        ]

    def create(self, validated_data):
        # user will come from view
        user = self.context["user"]  # pass via context
        profile_file = validated_data.pop("profile_image", None)

        instance = LandscaperProfile.objects.create(user=user, **validated_data)

        if profile_file:
            instance.profile_image = profile_file
            instance.save()

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["profile_image"] = instance.profile_image.url if instance.profile_image else None
        return data



import json
from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "landscaper",
            "standard_services",
            "custom_service",
            "description",
            "category",
            "add_ons",
            "latitude",
            "longitude",
            "price",
            "per_square_feet",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "landscaper",
            "created_at",
            "updated_at",
        ]

    def to_internal_value(self, data):
        """
        Allow JSON arrays from multipart/form-data
        """
        mutable_data = data.copy()

        for field in ("standard_services", "add_ons"):
            if field in mutable_data and isinstance(mutable_data[field], str):
                try:
                    mutable_data[field] = json.loads(mutable_data[field])
                except json.JSONDecodeError:
                    raise serializers.ValidationError({
                        field: "Invalid JSON format."
                    })

        return super().to_internal_value(mutable_data)

    def validate_standard_services(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError(
                "At least one standard service must be selected."
            )
        return value

    def validate_add_ons(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Add-ons must be a list.")

        for addon in value:
            if not isinstance(addon, dict):
                raise serializers.ValidationError(
                    "Each add-on must be an object."
                )
            if "name" not in addon or "price" not in addon:
                raise serializers.ValidationError(
                    "Each add-on must include name and price."
                )
        return value

    def validate(self, attrs):
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")

        if lat is None or lon is None:
            raise serializers.ValidationError(
                "Service location (latitude and longitude) is required."
            )

        if not (-90 <= lat <= 90):
            raise serializers.ValidationError(
                {"latitude": "Latitude must be between -90 and 90."}
            )

        if not (-180 <= lon <= 180):
            raise serializers.ValidationError(
                {"longitude": "Longitude must be between -180 and 180."}
            )

        return attrs



# # landscapers/serializers.py
from rest_framework import serializers
from .models import WorkingHours, DAYS_OF_WEEK

class WorkingHoursSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']
