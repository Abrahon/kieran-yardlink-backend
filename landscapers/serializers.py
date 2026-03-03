

from django.db import transaction
from .models import BusinessProfile,ClientCustomService
from services.serializers import ServiceSerializer
import json
from .models import Service
from rest_framework import serializers
from .models import WorkingHours, DAYS_OF_WEEK
import json
from .models import Addon
from services.models import Service  
from django.core.exceptions import ValidationError

from cloudinary.models import CloudinaryField


class BusinessLandscaperProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    insurance_doc = serializers.ImageField(required=False, allow_null=True)
    license_doc = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = BusinessProfile
        fields = [
            "business_name",
            "business_email",
            "business_phone",
            "tagline",
            "description",
            "latitude",
            "longitude",
            "profile_image",
            "quickbooks_connected",
            "insurance_doc",
            "license_doc",
            "is_profile_completed",
        ]
        read_only_fields = ["is_profile_completed", "quickbooks_connected"]

    def validate(self, attrs):
        """
        Ensure only one of insurance_doc or license_doc is uploaded
        """
        insurance = attrs.get("insurance_doc") or getattr(self.instance, "insurance_doc", None)
        license_doc = attrs.get("license_doc") or getattr(self.instance, "license_doc", None)

        if insurance and license_doc:
            raise ValidationError("You can upload either insurance OR license document, not both.")
        return attrs

    def create(self, validated_data):
        user = self.context["user"]  # pass user from view via context
        profile_image = validated_data.pop("profile_image", None)
        insurance_doc = validated_data.pop("insurance_doc", None)
        license_doc = validated_data.pop("license_doc", None)

        instance = BusinessProfile.objects.create(user=user, **validated_data)

        # Assign optional files if provided
        if profile_image:
            instance.profile_image = profile_image
        if insurance_doc:
            instance.insurance_doc = insurance_doc
        if license_doc:
            instance.license_doc = license_doc

        instance.save()
        return instance

    def update(self, instance, validated_data):
        profile_image = validated_data.pop("profile_image", None)
        insurance_doc = validated_data.pop("insurance_doc", None)
        license_doc = validated_data.pop("license_doc", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_image:
            instance.profile_image = profile_image
        if insurance_doc:
            instance.insurance_doc = insurance_doc
            instance.license_doc = None  # clear license if insurance is provided
        if license_doc:
            instance.license_doc = license_doc
            instance.insurance_doc = None  # clear insurance if license is provided

        instance.save()
        return instance



class ServiceSerializer(serializers.ModelSerializer):
    business = serializers.ReadOnlyField(source="business.id")

    class Meta:
        model = Service
        fields = [
            "id",
            "business",
            "name",
            "description",
            "base_price",
            "pricing_type",
            "min_price",
            "latitude",
            "longitude",
            "is_active",
            "is_pinned",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "business", "created_at", "updated_at", "is_pinned"]

    def validate(self, attrs):
        pricing_type = attrs.get("pricing_type")
        base_price = attrs.get("base_price")

        if pricing_type == "fixed" and base_price is None:
            raise serializers.ValidationError("Fixed pricing requires base_price.")

        if pricing_type == "request" and base_price is not None:
            raise serializers.ValidationError("Request pricing should not include base_price.")

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


class UpdateServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "custom_service",
            "description",
            "category",
            "price",
            "per_square_feet",
        ]




class ClientCustomServiceSerializer(serializers.ModelSerializer):
    client = serializers.ReadOnlyField(source="client.id")

    class Meta:
        model = ClientCustomService
        fields = [
            "id",
            "client",
            "name",
            "description",
            "price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "client", "created_at", "updated_at"]

    def validate_name(self, value):
        return value.strip()

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value






class AddonSerializer(serializers.ModelSerializer):
    business = serializers.ReadOnlyField(source="business.id")

    class Meta:
        model = Addon
        fields = [
            "id",
            "business",
            "name",
            "price",
            "applicable_service_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "business", "created_at", "updated_at"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def validate_applicable_service_ids(self, value):
        """
        Ensure all service IDs belong to this business.
        """
        request = self.context.get("request")
        if not request:
            return value

        try:
            business = request.user.landscaperprofilies
        except:
            return value

        valid_ids = set(
            Service.objects.filter(
                business=business,
                id__in=value
            ).values_list("id", flat=True)
        )

        if set(value) != valid_ids:
            raise serializers.ValidationError(
                "Some service IDs are invalid or do not belong to your business."
            )

        return value

# # landscapers/serializers.py
class WorkingHoursSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']




class StandardServiceSerializer(serializers.ModelSerializer):
    # Input in minutes
    time = serializers.IntegerField(
        write_only=True, required=True, help_text="Time in minutes"
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "standard_service",
            "description",
            "price",
            "rate_type",
            "latitude",
            "longitude",
            "time",       # input in minutes
            "is_active",
            "is_pinned",
        ]
        read_only_fields = ["is_active","is_pinned"]

    def create(self, validated_data):
        minutes = validated_data.pop("time")
        validated_data["time"] = round(minutes / 60, 2)  
        validated_data["category"] = Service.CategoryChoices.STANDARD
        validated_data["is_active"] = True
        validated_data["is_pinned"] = False 
        return super().create(validated_data)

    def update(self, instance, validated_data):
        minutes = validated_data.pop("time", None)
        if minutes is not None:
            validated_data["time"] = round(minutes / 60, 2)
        validated_data["category"] = Service.CategoryChoices.STANDARD
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["time"] = float(instance.time)  # display in hours
        return rep