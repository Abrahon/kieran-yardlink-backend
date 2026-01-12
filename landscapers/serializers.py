


from rest_framework import serializers
from django.db import transaction
from .models import LandscaperProfile
from services.models import Service
from services.serializers import ServiceSerializer

from .models import Service
import json

from rest_framework import serializers
from .models import LandscaperProfile

class LandscaperProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandscaperProfile
        fields = [
            "business_name",
            "business_email",
            "business_phone",
            "latitude",
            "longitude",
            "profile",  # this will automatically give the Cloudinary URL
        ]
    def get_profile(self, obj):
        """Return Cloudinary URL"""
        if obj.image:
            return obj.profile.url
        return None


# serializers

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
        read_only_fields = ["id", "landscaper", "created_at", "updated_at"]

    def to_internal_value(self, data):
        """Allow JSON arrays from multipart/form-data"""
        mutable_data = data.copy()

        for field in ["standard_services", "add_ons"]:
            if field in mutable_data and isinstance(mutable_data[field], str):
                try:
                    mutable_data[field] = json.loads(mutable_data[field])
                except json.JSONDecodeError:
                    raise serializers.ValidationError({
                        field: "Invalid JSON format"
                    })
        return super().to_internal_value(mutable_data)

    def validate_standard_services(self, value):
        if not value or not isinstance(value, list):
            raise serializers.ValidationError(
                "At least one standard service must be selected."
            )
        return value

# # landscapers/serializers.py
from rest_framework import serializers
from .models import WorkingHours, DAYS_OF_WEEK

class WorkingHoursSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']
