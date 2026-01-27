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



from landscapers.models import WorkingHours, LandscaperProfile, Service
from connections.models import ConnectionRequest
from django.db.models import Q


# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     image = serializers.ImageField(required=False, allow_null=True)
#     # already_sent = serializers.SerializerMethodField()  # NEW FIELD
    

#     # ✅ CORRECT & SIMPLE
#     business_name = serializers.CharField(
#         source="user.landscaper_profile.business_name",
#         read_only=True
#     )

#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id",
#             # "already_sent", 
#             "user_id",
#             "email",
#             "name",
#             "phone",
#             "image",
#             "business_name",
#             "working_hours",
#             "services",
#         ]

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data["image"] = instance.image.url if instance.image else None
#         return data
#     def get_working_hours(self, obj):
#         profile = getattr(obj.user, "landscaper_profile", None)
#         if not profile:
#             return []

#         return [
#             {
#                 "day": h.day,
#                 "start_time": h.start_time,
#                 "end_time": h.end_time,
#             }
#             for h in profile.working_hours.all().order_by("day")
#         ]
#     def get_services(self, obj):
#         services = Service.objects.filter(landscaper=obj.user)
#         return [
#             {
#                 "id": s.id,
#                 "category": s.category,
#                 "standard_services": s.standard_services,
#                 "custom_service": s.custom_service,
#                 "description": s.description,
#                 "price": float(s.price),
#                 "per_square_feet": float(s.per_square_feet),
#                 "latitude": float(s.latitude),
#                 "longitude": float(s.longitude),
#                 "add_ons": s.add_ons,
#             }
#             for s in services
#         ]
#     # def get_already_sent(self, obj):
#     #         """
#     #         Returns True if a request already exists between sender and receiver.
#     #         Includes all statuses: pending, accepted, rejected.
#     #         """
#     #         exists = ConnectionRequest.objects.filter(
#     #             Q(sender=obj.sender, receiver=obj.receiver) |
#     #             Q(sender=obj.receiver, receiver=obj.sender)
#     #         ).exists()
#     #         return exists
from rest_framework import serializers
from django.db.models import Q
from connections.models import ConnectionRequest
from landscapers.models import Service
from profiles.models import LandscaperProfilies


class LandscaperProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
   


    business_name = serializers.CharField(
        source="user.landscaper_profile.business_name",
        read_only=True
    )

    working_hours = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField()  # ✅ ADD THIS
    connection_request_id = serializers.SerializerMethodField()

    class Meta:
        model = LandscaperProfilies
        fields = [
            "id",
            "user_id",
            "email",
            "name",
            "phone",
            "image",
            "business_name",
            "working_hours",
            "services",
            "already_sent",
            "connection_request_id",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["image"] = instance.image.url if instance.image else None
        return data

    def get_working_hours(self, obj):
        profile = getattr(obj.user, "landscaper_profile", None)
        if not profile:
            return []

        return [
            {
                "day": h.day,
                "start_time": h.start_time,
                "end_time": h.end_time,
            }
            for h in profile.working_hours.all().order_by("day")
        ]

    def get_services(self, obj):
        services = Service.objects.filter(landscaper=obj.user)
        return [
            {
                "id": s.id,
                "category": s.category,
                "standard_services": s.standard_services,
                "custom_service": s.custom_service,
                "description": s.description,
                "price": float(s.price),
                "per_square_feet": float(s.per_square_feet),
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
                "add_ons": s.add_ons,
            }
            for s in services
        ]
    def get_connection_request_id(self, obj):

        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        connection = ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user),
            is_accepted__isnull=True  # pending only
        ).first()

        return connection.id if connection else None


    def get_already_sent(self, obj):
        """
        True if a connection request already exists
        between logged-in user and this landscaper
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user)
        ).exists()

# serializers.py


class ClientProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    services = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    total_service_price = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField()  # ✅ ADD THIS
    connection_request_id = serializers.SerializerMethodField()


    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "user_id",
            "email",
            "name",
            "phone",
            "image",
            "services",
            "total_service_price",
            "properties",
            "already_sent",
            "connection_request_id",
        ]

    def get_services(self, obj):
        services = Service.objects.filter(standard_services=True)
        return [
            {
                "id": s.id,
                "category": s.category,
                "standard_services": s.standard_services,
                "custom_service": s.custom_service,
                "price": float(s.price) if s.price else 0,
            }
            for s in services
        ]

    def get_total_service_price(self, obj):
        services = Service.objects.filter(standard_services=True)
        return sum(float(s.price or 0) for s in services)

    def get_properties(self, obj):
        properties = Property.objects.filter(owner=obj.user)
        return [
            {
                "address": p.address,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "property_size": p.property_size,
                "cut_height_inches": p.cut_height_inches,
                "grass_types": p.grass_types,
                "notes": p.notes,
                "images": p.images,
            }
            for p in properties
        ]

    def get_already_sent(self, obj):
            """
            Returns True if a connection request already exists
            between logged-in user and this client
            """
            request = self.context.get("request")
            if not request or not request.user.is_authenticated:
                return False

            return ConnectionRequest.objects.filter(
                Q(sender=request.user, receiver=obj.user) |
                Q(sender=obj.user, receiver=request.user)
            ).exists()
            
    def get_connection_request_id(self, obj):
            
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        connection = ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user),
            is_accepted__isnull=True
        ).first()

        return connection.id if connection else None



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
    
# profiles/serializers.py
from rest_framework import serializers
from profiles.models import LandscaperProfilies

class ConnectedUserSerializer(serializers.Serializer):
    """
    Serializer to return a connected user's profile and connection id.
    """
    connection_id = serializers.IntegerField()
    connected_profile = serializers.DictField()  # serialized profile data
    created_at = serializers.DateTimeField()
