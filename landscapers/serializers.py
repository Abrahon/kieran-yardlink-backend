

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
from profiles.models import ClientProfile
from landscapers.models import BusinessProfile
from rest_framework import serializers

from profiles.models import ClientProfile
from .models import ClientCustomService
from property.models import Property
from cloudinary.models import CloudinaryField
# from profiles.serializers import ClientProfileSerializer
# from landscapers.serializers import WorkingHoursSerializer

from property.serializers import PropertySerializer

class BusinessLandscaperProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    insurance_doc = serializers.ImageField(required=False, allow_null=True)
    license_doc = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = BusinessProfile
        fields = [
            "id",
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
        request = self.context.get("request")
        user = request.user

        if hasattr(user, "landscaper_profile"):
            raise ValidationError("Business profile already exists.")

        profile_image = validated_data.pop("profile_image", None)
        insurance_doc = validated_data.pop("insurance_doc", None)
        license_doc = validated_data.pop("license_doc", None)

        instance = BusinessProfile.objects.create(
            user=user,
            **validated_data
        )

        if profile_image:
            instance.profile_image = profile_image
        if insurance_doc:
            instance.insurance_doc = insurance_doc
        if license_doc:
            instance.license_doc = license_doc

        instance.save()
        return instance

    def update(self, instance, validated_data):
        # -----------------------------
        # Update business profile fields
        # -----------------------------
        instance.latitude = validated_data.get("latitude", instance.latitude)
        instance.longitude = validated_data.get("longitude", instance.longitude)

        profile_image = validated_data.get("profile_image")
        if profile_image is not None:
            instance.profile_image = profile_image

        instance.save()

        # -----------------------------
        # Update personal profile fields (LandscaperProfilies)
        # -----------------------------
        # Get or create personal profile
        personal_profile, created = LandscaperProfilies.objects.get_or_create(user=instance.user)

        name = validated_data.get("name")
        phone = validated_data.get("phone")
        if name is not None:
            personal_profile.name = name
        if phone is not None:
            personal_profile.phone = phone

        personal_profile.save()

        return instance
    def update(self, instance, validated_data):
        for field in [
            "business_name",
            "business_email",
            "business_phone",
            "tagline",
            "description",
            "latitude",
            "longitude",
            "profile_image",
            "insurance_doc",
            "license_doc",
        ]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance


# class ServiceSerializer(serializers.ModelSerializer):
#     business = serializers.ReadOnlyField(source="business.id")

#     class Meta:
#         model = Service
#         fields = [
#             "id", "business", "name", "description",
#             "base_price", "pricing_type", "min_price",
#             "latitude", "longitude", "is_active", "is_pinned",
#             "created_at", "updated_at",
#         ]
#         read_only_fields = ["id", "business", "created_at", "updated_at", "is_pinned"]
#     def validate_name(self, value):
#         request = self.context.get("request")
#         if not request:
#             raise serializers.ValidationError("Request context is missing.")

#         user = getattr(request, "user", None)
#         if not user or not user.is_authenticated:
#             raise serializers.ValidationError("Authentication required.")

#         # Correct way to get business
#         business = getattr(user, "landscaper_profile", None)
#         if not business:
#             raise serializers.ValidationError(
#                 "You must have a business profile to create services."
#             )

#         # Skip check if unchanged (PATCH safe)
#         if self.instance and self.instance.name == value:
#             return value

#         if Service.objects.filter(
#             business=business,
#             name=value
#         ).exclude(
#             id=getattr(self.instance, "id", None)
#         ).exists():
#             raise serializers.ValidationError(
#                 "A service with this name already exists for your business."
#             )

#         return value
        
#     def validate(self, attrs):
#         # Pricing rules
#         pricing_type = attrs.get("pricing_type", getattr(self.instance, 'pricing_type', None))
#         base_price = attrs.get("base_price", getattr(self.instance, 'base_price', None))

#         if pricing_type == "fixed" and base_price is None:
#             raise serializers.ValidationError("Fixed pricing requires base_price.")

#         if pricing_type == "request" and base_price is not None:
#             raise serializers.ValidationError("Request pricing should not include base_price.")

#         # Latitude/Longitude rules
#         lat = attrs.get("latitude", getattr(self.instance, 'latitude', None))
#         lon = attrs.get("longitude", getattr(self.instance, 'longitude', None))

#         if lat is None or lon is None:
#             raise serializers.ValidationError(
#                 "Service location (latitude and longitude) is required."
#             )

#         if not (-90 <= lat <= 90):
#             raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})

#         if not (-180 <= lon <= 180):
#             raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})

#         return attrs  

class ServiceSerializer(serializers.ModelSerializer):
    business = serializers.ReadOnlyField(source="business.id")

    class Meta:
        model = Service
        fields = [
            "id", "business", "name", "description",
            "base_price", "pricing_type", "min_price",
            "latitude", "longitude", "is_active", "is_pinned",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "business", "created_at", "updated_at", "is_pinned"]

    def validate_name(self, value):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is missing.")

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        try:
            business = BusinessProfile.objects.get(user=user)
        except BusinessProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must have a business profile to create services."
            )

        if self.instance and self.instance.name == value:
            return value

        if Service.objects.filter(
            business=business,
            name=value
        ).exclude(
            id=getattr(self.instance, "id", None)
        ).exists():
            raise serializers.ValidationError(
                "A service with this name already exists for your business."
            )

        return value

    def validate(self, attrs):
        pricing_type = attrs.get("pricing_type", getattr(self.instance, "pricing_type", None))
        base_price = attrs.get("base_price", getattr(self.instance, "base_price", None))

        if pricing_type == "fixed" and base_price is None:
            raise serializers.ValidationError("Fixed pricing requires base_price.")

        if pricing_type == "request" and base_price is not None:
            raise serializers.ValidationError("Request pricing should not include base_price.")

        lat = attrs.get("latitude", getattr(self.instance, "latitude", None))
        lon = attrs.get("longitude", getattr(self.instance, "longitude", None))

        if lat is None or lon is None:
            raise serializers.ValidationError(
                "Service location (latitude and longitude) is required."
            )

        if not (-90 <= lat <= 90):
            raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})

        if not (-180 <= lon <= 180):
            raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})

        return attrs



# -------------------------
# CLIENT (FULL PROFILE)
# -------------------------
# class ClientProfileMiniSerializer(serializers.ModelSerializer):
#     name = serializers.CharField(source="user.name", read_only=True)
#     email = serializers.CharField(source="user.email", read_only=True)

#     class Meta:
#         model = ClientProfile
#         fields = ["id", "name", "email"]

# class ClientCustomServiceSerializer(serializers.ModelSerializer):
#     client = ClientProfileMiniSerializer(read_only=True)
#     property = PropertyMiniSerializer(read_only=True)

#     booking_id = serializers.ReadOnlyField(source="booking.id")

#     class Meta:
#         model = ClientCustomService
#         fields = [
#             "id", "client", "landscaper", "property", "name", "description", "note",
#             "price", "status", "is_active",

#             # ✅ allow these fields
#             "preferred_date", "preferred_time",

#             "recurring_type", "recurring_day_of_week",
#             "booking_id",
#             "created_at", "updated_at"
#         ]

#         read_only_fields = [
#             "id", "client",
#             "booking_id",
#             "created_at", "updated_at",
#         ]
#     def validate(self, attrs):
#         recurring_type = attrs.get("recurring_type")
#         recurring_day_of_week = attrs.get("recurring_day_of_week")

#         preferred_date = attrs.get("preferred_date")
#         preferred_time = attrs.get("preferred_time")

#         # -------------------------
#         # ONE-TIME SERVICE
#         # -------------------------
#         if not recurring_type:
#             if recurring_day_of_week:
#                 raise serializers.ValidationError(
#                     "One-time service cannot have day of week."
#                 )

#             if preferred_time and not preferred_date:
#                 raise serializers.ValidationError(
#                     "Preferred time requires a preferred date."
#                 )

#         # -------------------------
#         # RECURRING SERVICE
#         # -------------------------
#         else:
#             if recurring_type not in ["weekly", "biweekly"]:
#                 raise serializers.ValidationError("Invalid recurring type.")

#             if not recurring_day_of_week:
#                 raise serializers.ValidationError(
#                     "Recurring service must include day of week."
#                 )

#             if not preferred_date:
#                 raise serializers.ValidationError(
#                     "Recurring service must include a start date (preferred_date)."
#                 )

#             # ✅ DO NOTHING HERE (IMPORTANT)
#             # allow preferred_time to pass through

#         return attrs



class ClientProfileMiniSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = ClientProfile
        fields = ["id", "name", "email"]

# from rest_framework import serializers
from profiles.models import LandscaperProfilies


class LandscaperProfileMiniSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = LandscaperProfilies
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "profile_image",
        ]


# -------------------------
# MAIN SERIALIZER
# -------------------------
class ClientCustomServiceSerializer(serializers.ModelSerializer):

    client = ClientProfileMiniSerializer(read_only=True)
    landscaper = serializers.SerializerMethodField()
    property = PropertySerializer(read_only=True)
    booking_id = serializers.ReadOnlyField(source="booking.id")

    class Meta:
        model = ClientCustomService
        fields = [
            "id",
            "client",
            "landscaper",
            "property",

            "name",
            "description",
            "note",
            "price",
            "status",
            "is_active",

            "preferred_date",
            "preferred_time",

            "recurring_type",
            "recurring_day_of_week",

            "booking_id",
            "created_at",
            "updated_at"
        ]

        read_only_fields = [
            "id",
            "client",
            "booking_id",
            "created_at",
            "updated_at",
        ]

    def get_landscaper(self, obj):
        try:
            user = obj.landscaper.user

            return {
                "id": obj.landscaper.id,
                "name": getattr(user, "name", None) or getattr(user, "email", None),
                "email": getattr(user, "email", None),
            }
        except Exception:
            return None
    # -------------------------
    # VALIDATION (FIXED)
    # -------------------------
    def validate(self, attrs):
        recurring_type = attrs.get("recurring_type")
        recurring_day_of_week = attrs.get("recurring_day_of_week")
        preferred_date = attrs.get("preferred_date")
        preferred_time = attrs.get("preferred_time")

        # -------------------------
        # ONE-TIME SERVICE
        # -------------------------
        if not recurring_type:

            if recurring_day_of_week:
                raise serializers.ValidationError(
                    "One-time service cannot have day of week."
                )

            if not preferred_date or not preferred_time:
                raise serializers.ValidationError(
                    "One-time service requires both date and time."
                )

        # -------------------------
        # RECURRING SERVICE
        # -------------------------
        else:

            if recurring_type not in ["weekly", "biweekly"]:
                raise serializers.ValidationError("Invalid recurring type.")

            if not recurring_day_of_week:
                raise serializers.ValidationError(
                    "Recurring service must include day of week."
                )

            if not preferred_date:
                raise serializers.ValidationError(
                    "Recurring service must include a start date."
                )

        return attrs

class AddonSerializer(serializers.ModelSerializer):
    business = serializers.ReadOnlyField(source="business.id")
    applicable_services = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Service.objects.all()
    )

    class Meta:
        model = Addon
        fields = [
            "id",
            "business",
            "name",
            "price",
            "applicable_services",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "business", "created_at", "updated_at"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be zero or positive.")
        return value

    def validate_applicable_services(self, services):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context not available.")

        try:
            business = request.user.landscaper_profile  # ✅ Correct related name
        except BusinessProfile.DoesNotExist:
            raise serializers.ValidationError("Landscaper profile not found.")

        # Ensure all services belong to this business
        for service in services:
            if service.business != business:
                raise serializers.ValidationError(
                    f"Service '{service.name}' does not belong to your business."
                )
        return services



# client
class PublicServiceSerializer(serializers.ModelSerializer):
    business_id = serializers.IntegerField(source="business.id", read_only=True)
    business_name = serializers.CharField(source="business.business_name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "business_id",
            "business_name",
            "name",
            "description",
            "base_price",
            "pricing_type",
            "min_price",
            "latitude",
            "longitude",
            "is_active",
        ]


class PublicAddonSerializer(serializers.ModelSerializer):
    business_id = serializers.IntegerField(source="business.id", read_only=True)
    business_name = serializers.CharField(source="business.business_name", read_only=True)

    class Meta:
        model = Addon
        fields = [
            "id",
            "business_id",
            "business_name",
            "name",
            "price",
            "is_active",
        ]

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