from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdminProfile,ClientProfile,WorkerProfile,ClientProfile,LandscaperProfilies
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from .models import WorkerProfile
from rest_framework import serializers
from .models import ClientProfile
from services.models import Service
from property.models import Property

User = get_user_model()

class AdminProfileSerializer(serializers.ModelSerializer):
    # Read-only fields from User model
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    # Image field for upload (Cloudinary)
    image = serializers.ImageField(required=False)

    class Meta:
        model = AdminProfile
        fields = ["name", "email", "role", "phone", "image"]
        read_only_fields = ["name", "email", "role"]

    def get_image(self, obj):
        """Return Cloudinary URL"""
        if obj.image:
            return obj.image.url
        return None

    def update(self, instance, validated_data):
        # Update phone
        instance.phone = validated_data.get("phone", instance.phone)

        # Update image if provided
        image = validated_data.get("image")
        if image:
            instance.image = image  # Cloudinary handles upload automatically

        instance.save()
        return instance




class WorkerProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()  # override image to return URL

    class Meta:
        model = WorkerProfile
        fields = ["email", "name", "phone", "image","is_blocked"]

    def get_email(self, obj):
        return obj.user.email

    def get_image(self, obj):
        if obj.image:
            return obj.image.url  # return full Cloudinary URL
        return None





from rest_framework import serializers
from landscapers.models import LandscaperProfile, WorkingHours
from .models import LandscaperProfilies  # <- use the correct model name

class LandscaperProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.ImageField(required=False)

    # Business name from LandscaperProfile model
    business_name = serializers.SerializerMethodField()

    # Working hours from WorkingHours model
    working_hours = serializers.SerializerMethodField()

    class Meta:
        model = LandscaperProfilies  # <- match your actual model
        fields = [
            "email",
            "name",
            "phone",
            "image",
            "business_name",
            "working_hours",
        ]

    def get_business_name(self, obj):
        try:
            profile = LandscaperProfile.objects.get(user=obj.user)
            return profile.business_name
        except LandscaperProfile.DoesNotExist:
            return None

    def get_working_hours(self, obj):
        try:
            profile = LandscaperProfile.objects.get(user=obj.user)
            hours = profile.working_hours.all().order_by("day")
            return [
                {
                    "day": h.day,
                    "start_time": h.start_time,
                    "end_time": h.end_time
                }
                for h in hours
            ]
        except LandscaperProfile.DoesNotExist:
            return []


# serializers.py
class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    
    # Change here: use actual field instead of SerializerMethodField
    image = serializers.ImageField(required=False, allow_null=True)

    services = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    total_service_price = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "email",
            "name",
            "phone",
            "image",  # now updatable
            "services",
            "total_service_price",
            "properties",
           
        ]

    # ---------------- Standard Services ----------------
    def get_services(self, obj):
        from services.serializers import ServiceSerializer

        services_qs = Service.objects.filter(is_standard=True)
        data = ServiceSerializer(services_qs, many=True).data

        return [
            {
                "category": s["category"],
                "name": s["name"],
                "price": s["price"],
            }
            for s in data
        ]

    # ---------------- Total Price ----------------
    def get_total_service_price(self, obj):
        services_qs = Service.objects.filter(is_standard=True)
        total = sum(s.price or 0 for s in services_qs)
        return total

    # ---------------- Client Properties ----------------
    def get_properties(self, obj):
        from property.serializers import PropertySerializer

        properties_qs = Property.objects.filter(owner=obj.user)
        data = PropertySerializer(properties_qs, many=True).data

        return [
            {
                "address": p["address"],
                "latitude": p["latitude"],
                "longitude": p["longitude"],
                "property_size": p["property_size"],
                "cut_height_inches": p["cut_height_inches"],
                "grass_types": p["grass_types"],
                "notes": p["notes"],
                "images": p["images"],
            }
            for p in data
        ]

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'},
        error_messages={'required': _('Current password is required')}
    )
    new_password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        error_messages={'required': _('New password is required')}
    )
    confirm_new_password = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'},
        error_messages={'required': _('Please confirm your new password')}
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Current password is incorrect'))
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': _('New passwords do not match')})
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': _('New password cannot be the same as the current password')})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user