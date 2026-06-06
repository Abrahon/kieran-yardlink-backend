

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
from subscriptions.helpers import get_landscaper_plan
from profiles.models import ClientProfile
from .models import ClientCustomService
from property.models import Property
from cloudinary.models import CloudinaryField
from rest_framework import serializers
from .models import ServiceQuote
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
            "service_radius_km",
            "profile_image",
            "quickbooks_connected",
            "insurance_doc",
            "license_doc",
            "is_profile_completed",
        ]
        read_only_fields = ["is_profile_completed", "quickbooks_connected"]

    # -----------------------------
    # PLAN-BASED FIELD VALIDATION
    # -----------------------------
    def validate_profile_image(self, value):
        user = self.context["request"].user

        if get_landscaper_plan(user) == "basic":
            raise serializers.ValidationError(
                "Profile image is only available in Pro plan"
            )
        return value

    def validate(self, attrs):
        """
        Ensure only one of insurance_doc or license_doc is uploaded
        """
        insurance = attrs.get("insurance_doc") or getattr(self.instance, "insurance_doc", None)
        license_doc = attrs.get("license_doc") or getattr(self.instance, "license_doc", None)

        if insurance and license_doc:
            raise serializers.ValidationError(
                "You can upload either insurance OR license document, not both."
            )

        return attrs


    # def create(self, validated_data):
    #     request = self.context.get("request")
    #     user = request.user

    #     if hasattr(user, "landscaper_profile"):
    #         raise ValidationError("Business profile already exists.")

    #     profile_image = validated_data.pop("profile_image", None)
    #     insurance_doc = validated_data.pop("insurance_doc", None)
    #     license_doc = validated_data.pop("license_doc", None)

    #     instance = BusinessProfile.objects.create(
    #         user=user,
    #         **validated_data
    #     )

    #     if profile_image:
    #         instance.profile_image = profile_image
    #     if insurance_doc:
    #         instance.insurance_doc = insurance_doc
    #     if license_doc:
    #         instance.license_doc = license_doc

    #     instance.save()
    #     return instance

    # -----------------------------
    # CREATE
    # -----------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        if hasattr(user, "landscaper_profile"):
            raise serializers.ValidationError("Business profile already exists.")

        return BusinessProfile.objects.create(user=user, **validated_data)



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


# models.py

# serializers.py

from rest_framework import serializers


class ServiceSerializer(serializers.ModelSerializer):

    business = serializers.ReadOnlyField(
        source="business.id"
    )

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
            "is_active",
            "is_pinned",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "business",
            "created_at",
            "updated_at",
            "is_pinned",
        ]

    def validate_name(self, value):

        request = self.context.get("request")

        if not request:
            raise serializers.ValidationError(
                "Request context is missing."
            )

        user = request.user

        if not user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication required."
            )

        try:
            business = BusinessProfile.objects.get(user=user)

        except BusinessProfile.DoesNotExist:
            raise serializers.ValidationError(
                "You must have a business profile to create services."
            )

        # allow same name on update
        if self.instance and self.instance.name == value:
            return value

        exists = Service.objects.filter(
            business=business,
            name=value
        ).exclude(
            id=getattr(self.instance, "id", None)
        ).exists()

        if exists:
            raise serializers.ValidationError(
                "A service with this name already exists for your business."
            )

        return value

    def validate(self, attrs):

        pricing_type = attrs.get(
            "pricing_type",
            getattr(self.instance, "pricing_type", None)
        )

        base_price = attrs.get(
            "base_price",
            getattr(self.instance, "base_price", None)
        )

        min_price = attrs.get(
            "min_price",
            getattr(self.instance, "min_price", None)
        )

        # FIXED pricing validation
        if pricing_type == Service.PricingType.FIXED:

            if base_price is None:
                raise serializers.ValidationError(
                    {
                        "base_price": "Fixed pricing requires base_price."
                    }
                )

            attrs["min_price"] = None

        # REQUEST pricing validation
        if pricing_type == Service.PricingType.REQUEST:

            if base_price is not None:
                raise serializers.ValidationError(
                    {
                        "base_price": "Request pricing should not include base_price."
                    }
                )

            if min_price is None:
                raise serializers.ValidationError(
                    {
                        "min_price": "Request pricing requires min_price."
                    }
                )

        return attrs

# -------------------------
# CLIENT (FULL PROFILE)


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

    landscaper = serializers.PrimaryKeyRelatedField(
        queryset=BusinessProfile.objects.all()
    )

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
            business = request.user.landscaper_profile  
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




# serializers.py

class ServiceQuoteSerializer(serializers.ModelSerializer):

    client = ClientProfileMiniSerializer(read_only=True)

    # ✅ FULL SERVICE RESPONSE
    service = ServiceSerializer(read_only=True)

    # ✅ FULL PROPERTY RESPONSE
    property = PropertySerializer(read_only=True)

    # ✅ INPUT FIELD
    property_id = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all(),
        source="property",
        write_only=True
    )

    # ✅ INPUT FIELD
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source="service",
        write_only=True
    )
    request_type = serializers.SerializerMethodField()  # ✅ ADD HERE
    landscaper = serializers.SerializerMethodField()

    class Meta:
        model = ServiceQuote

        fields = [
            "id",

            # SERVICE
            "service",
            "service_id",

            # CLIENT
            "client",

            # LANDSCAPER
            "landscaper",

            # PROPERTY
            "property",
            "property_id",

            # MESSAGE
            "message",

            # CLIENT PREFERRED
            "preferred_date",
            "preferred_time",

            # LANDSCAPER CONFIRMED
            "scheduled_date",
            "scheduled_time",

            # PRICE
            "price",
            "request_type",  # ✅ ADD TO FIELDS
            # STATUS
            "status",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "client",
            "landscaper",
            "price",
            "status",
            "created_at",
            "updated_at",
        ]

    # =====================================
    # LANDSCAPER INFO (FIXED)
    # =====================================

    def get_landscaper(self, obj):
        landscaper = obj.landscaper

        if not landscaper:
            return None

        user = landscaper.user
        profile = getattr(user, "landscaperprofilies", None)

        return {
            "id": landscaper.id,

            # ✅ FIX HERE (IMPORTANT)
            "name": user.name or getattr(profile, "name", None),

            "email": user.email,

            "phone": getattr(profile, "phone", None),
            "address": getattr(profile, "address", None),

            "profile_image": (
                profile.profile_image.url
                if profile and getattr(profile, "profile_image", None)
                else None
            ),
        }
    def get_request_type(self, obj):
        return getattr(obj, "request_type", "quote_request")
    # =====================================
    # VALIDATION
    # =====================================

    def validate(self, data):

        service = data.get("service")

        if not service:
            raise serializers.ValidationError({
                "service_id": "Service is required."
            })

        if service.pricing_type != Service.PricingType.REQUEST:
            raise serializers.ValidationError({
                "service_id": "Quote requests allowed only for request pricing services."
            })

        return data

    # =====================================
    # CREATE
    # =====================================

    def create(self, validated_data):

        request = self.context["request"]

        client = getattr(request.user, "clientprofile", None)

        if not client:
            raise serializers.ValidationError({
                "error": "Client profile not found."
            })

        service = validated_data["service"]

        validated_data["client"] = client
        validated_data["landscaper"] = service.business
        validated_data["status"] = ServiceQuote.Status.PENDING
        validated_data["price"] = None

        return ServiceQuote.objects.create(**validated_data)