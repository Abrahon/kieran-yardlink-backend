# from rest_framework import serializers
# from .models import LandscaperProfile
# from services.models import Service
# from services.serializers import ServiceSerializer

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     services = ServiceSerializer(many=True)
#     profile_url = serializers.SerializerMethodField()  # to return Cloudinary URL

#     class Meta:
#         model = LandscaperProfile
#         fields = [
#             "business_name",
#             "business_email",
#             "business_phone",
#             "service_address",
#             "latitude",
#             "longitude",
#             "services",
#             "profile",       # raw Cloudinary field
#             "profile_url",   # URL for frontend
#         ]

#     def get_profile_url(self, obj):
#         if obj.profile:
#             return obj.profile.url
#         return None

#     def create(self, validated_data):
#         services_data = validated_data.pop("services")
#         image = validated_data.pop("profile", None)  # handle image

#         user = self.context["request"].user

#         profile = LandscaperProfile.objects.create(
#             user=user,
#             is_profile_completed=True,
#             **validated_data
#         )

#         if image:
#             profile.profile = image  # Cloudinary handles upload automatically
#             profile.save()

#         for service in services_data:
#             Service.objects.create(
#                 landscaper=profile,
#                 **service
#             )

#         return profile


# # working hours serializers


from rest_framework import serializers
from django.db import transaction
from .models import LandscaperProfile
from services.models import Service
from services.serializers import ServiceSerializer


# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     services = ServiceSerializer(many=True, required=False)
#     profile_url = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfile
#         fields = [
#             "business_name",
#             "business_email",
#             "business_phone",
#             "service_address",
#             "latitude",
#             "longitude",
#             "services",
#             "profile",
#             "profile_url",
#         ]

#     def get_profile_url(self, obj):
#         return obj.profile.url if obj.profile else None

#     @transaction.atomic
#     def create(self, validated_data):
#         services_data = validated_data.pop("services", [])
#         image = validated_data.pop("profile", None)

#         user = self.context["request"].user

#         profile = LandscaperProfile.objects.create(
#             user=user,
#             is_profile_completed=True,
#             **validated_data
#         )

#         if image:
#             profile.profile = image
#             profile.save(update_fields=["profile"])

#         for service in services_data:
#             Service.objects.create(
#                 landscaper=profile,
#                 **service
#             )

#         return profile
from rest_framework import serializers
from django.db import transaction
from .models import LandscaperProfile

from rest_framework import serializers
from .models import LandscaperProfile
import json

class LandscaperProfileSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = LandscaperProfile
        fields = [
            "business_name",
            "business_email",
            "business_phone",
            "service_address",
            "latitude",
            "longitude",
            "standard_services",
            "add_ons",
            "profile",
            "profile_url",
        ]

    def get_profile_url(self, obj):
        return obj.profile.url if obj.profile else None

    def validate_standard_services(self, value):
        if not value or not isinstance(value, list):
            raise serializers.ValidationError(
                "At least one standard service is required."
            )
        return value

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

# serializers
from rest_framework import serializers
from .models import Service
import json

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
