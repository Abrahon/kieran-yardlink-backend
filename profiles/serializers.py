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


# profiles/serializers.py
# from rest_framework import serializers
# from landscapers.models import WorkingHours, LandscaperProfile

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(read_only=True)
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     image = serializers.ImageField(required=False)

#     business_name = serializers.CharField(
#         source="user.landscaperprofile.business_name",
#         read_only=True
#     )

#     working_hours = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id",
#             "user_id",
#             "email",
#             "name",
#             "phone",
#             "image",
#             "business_name",
#             "working_hours",
#         ]

#     def get_working_hours(self, obj):
#         # obj is LandscaperProfilies instance
#         try:
#             # Get the corresponding landscaper profile from landscapers app
#             profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             return []

#         hours = profile.working_hours.all().order_by("day")
#         return [
#             {
#                 "day": h.day,
#                 "start_time": h.start_time,
#                 "end_time": h.end_time
#             }
#             for h in hours
#         ]
# profiles/serializers.py
from rest_framework import serializers
from landscapers.models import WorkingHours, LandscaperProfile, Service
from .models import LandscaperProfilies

class LandscaperProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.ImageField(required=False)

    business_name = serializers.CharField(
        source="user.landscaperprofile.business_name",
        read_only=True
    )

    working_hours = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()  # Add services

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
            "services",  # include here
        ]

#     from rest_framework import serializers
# from landscapers.models import WorkingHours, LandscaperProfile, Service
# from .models import LandscaperProfilies

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(read_only=True)
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     image = serializers.ImageField(required=False)

#     business_name = serializers.CharField(
#         source="user.landscaperprofile.business_name",
#         read_only=True
#     )

#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()  # Add services

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id",
#             "user_id",
#             "email",
#             "name",
#             "phone",
#             "image",
#             "business_name",
#             "working_hours",
#             "services",  # include here
#         ]

#     def get_working_hours(self, obj):
#         try:
#             profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             return []

#         hours = profile.working_hours.all().order_by("day")
#         return [
#             {
#                 "day": h.day,
#                 "start_time": h.start_time,
#                 "end_time": h.end_time
#             }
#             for h in hours
#         ]


#     def get_services(self, obj):
#         try:
#             profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             return []

#         # Now filter services linked to this landscaper profile
#         services = Service.objects.filter(landscaper=profile)

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

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(read_only=True)
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     image = serializers.ImageField(required=False)
#     business_name = serializers.CharField(source="user.landscaperprofile.business_name", read_only=True)
#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id", "user_id", "email", "name", "phone", "image",
#             "business_name", "working_hours", "services",
#         ]

#     def get_working_hours(self, obj):
#         try:
#             # get landscaper profile from landscapers app
#             profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             return []  # return empty if no landscaper profile exists

#         # get working hours
#         return [
#             {"day": h.day, "start_time": h.start_time, "end_time": h.end_time}
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
# from rest_framework import serializers
# from landscapers.models import WorkingHours, LandscaperProfile, Service
# from .models import LandscaperProfilies

# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(read_only=True)
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     image = serializers.ImageField(required=False)
#     business_name = serializers.CharField(
#         source="user.landscaperprofile.business_name",
#         read_only=True
#     )
#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id", "user_id", "email", "name", "phone", "image",
#             "business_name", "working_hours", "services",
#         ]

#     def get_working_hours(self, obj):
#         try:
#             # try to get the landscaper profile
#             landscaper_profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             # if deleted or missing, return empty list
#             return []

#         return [
#             {"day": h.day, "start_time": h.start_time, "end_time": h.end_time}
#             for h in landscaper_profile.working_hours.all().order_by("day")
#         ]

#     def get_services(self, obj):
#         try:
#             # make sure the landscaper profile exists
#             landscaper_profile = LandscaperProfile.objects.get(user=obj.user)
#         except LandscaperProfile.DoesNotExist:
#             # if missing, return empty list
#             return []

#         # fetch services linked to this user
#         services = Service.objects.filter(landscaper=obj.user)

#         return [
#             {
#                 "id": s.id,
#                 "category": s.category,
#                 "standard_services": getattr(s, "standard_services", []),
#                 "custom_service": s.custom_service,
#                 "description": s.description,
#                 "price": float(s.price),
#                 "per_square_feet": float(s.per_square_feet),
#                 "latitude": float(s.latitude),
#                 "longitude": float(s.longitude),
#                 "add_ons": getattr(s, "add_ons", []),
#             }
#             for s in services
#         ]
from rest_framework import serializers
from profiles.models import LandscaperProfilies

class LandscaperProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    business_name = serializers.CharField(source="user.landscaperprofile.business_name", read_only=True)
    working_hours = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = LandscaperProfilies
        fields = [
            "id", "user_id", "email", "name", "phone", "image",
            "business_name", "working_hours", "services"
        ]

    def get_working_hours(self, obj):
        try:
            profile = obj.user.landscaperprofile
            hours = profile.working_hours.all().order_by("day")
            return [{"day": h.day, "start_time": h.start_time, "end_time": h.end_time} for h in hours]
        except:
            return []

    def get_services(self, obj):
        try:
            profile = obj.user.landscaperprofile
            services = profile.user.services.all()
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
        except:
            return []

# serializers.py
from rest_framework import serializers
from .models import ClientProfile
from services.models import Service
from property.models import Property


class ClientProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)                  # profile id
    user_id = serializers.IntegerField(source="user.id", read_only=True)  # ✅ REQUIRED
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    services = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    total_service_price = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id",          # profile id
            "user_id",     # ✅ send THIS in connection request
            "email",
            "name",
            "phone",
            "image",
            "services",
            "total_service_price",
            "properties",
        ]

    def get_services(self, obj):
        services = Service.objects.filter(is_standard=True)
        return [
            {
                "category": s.category,
                "name": s.name,
                "price": s.price,
            }
            for s in services
        ]

    def get_total_service_price(self, obj):
        return sum(s.price or 0 for s in Service.objects.filter(is_standard=True))

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
