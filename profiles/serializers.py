from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdminProfile,ClientProfile,WorkerProfile,ClientProfile,LandscaperProfilies
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from .models import WorkerProfile
from rest_framework import serializers
from .models import ClientProfile
from rest_framework import serializers
from .models import ClientProfile
from property.models import Property
from reviews.models import LandscaperReview
from reviews.serializers import LandscaperReviewSerializer
from rest_framework import serializers
from django.db.models import Q
from connections.models import ConnectionRequest
from django.db.models import Avg
from landscapers.models import WorkingHours, BusinessProfile
from landscapers.serializers import WorkingHoursSerializer as WHSerializer
from landscapers.models import WorkingHours, BusinessProfile, Service
from services.models import ClientService 
from connections.models import ConnectionRequest
from subscriptions.models import Plan,Subscription
from subscriptions.enums import SubscriptionStatus
# from profiles.models import BusinessProfile
from geopy.geocoders import Nominatim
from django.utils import timezone
from invitations.models import TeamInvitation, InvitationStatus
from django.utils import timezone
from rest_framework import serializers
from django.db.models import Avg
from geopy.geocoders import Nominatim
from landscapers.serializers import WorkingHoursSerializer

from rest_framework import serializers
from django.db.models import Avg
from django.utils import timezone
from landscapers.models import BusinessProfile
from subscriptions.models import Subscription, SubscriptionStatus
from jobs.models import Job
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
            instance.image = image  

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

            return obj.image.url
              # return full Cloudinary URL



class LandscaperPersonalProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    profile_image = serializers.ImageField(
        source="image",
        required=False,
        allow_null=True
    )

    business_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()

    class Meta:
        model = LandscaperProfilies
        fields = [
            "email",
            "name",
            "phone",
            "profile_image",
            "business_name",
            "address",
            "subscription",
        ]


    def get_subscription(self, obj):
        user = getattr(obj, "user", obj)

        sub_qs = Subscription.objects.filter(user=user)

        active_sub = sub_qs.filter(
            status__in=["active", "trialing"]
        ).order_by("-end_date").first()

        if not active_sub:
            return {
                "plan_type": None,
                "start_date": None,
                "end_date": None,
                "remaining_days": 0,
                "is_trial": False
            }

        now = timezone.now()

        remaining_days = 0
        if active_sub.end_date:
            remaining_days = max(0, (active_sub.end_date - now).days)

        return {
            "plan_type": active_sub.plan.name if active_sub.plan else None,
            "start_date": active_sub.start_date,
            "end_date": active_sub.end_date,
            "remaining_days": remaining_days,
            "is_trial": active_sub.status == "trialing"
        }
        # -------------------------
    # UPDATE
    # -------------------------
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.phone = validated_data.get("phone", instance.phone)

        if "image" in validated_data:
            instance.image = validated_data["image"]

        instance.save()
        return instance
    

    # -------------------------
    # IMAGE FIX
    # -------------------------
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["profile_image"] = instance.image.url if instance.image else None
        return data

    # -------------------------
    # BUSINESS HELPERS
    # -------------------------
    def get_business_profile(self, obj):
        try:
            return obj.user.landscaper_profile  # BusinessProfile
        except Exception:
            return None

    def get_business_name(self, obj):
        bp = self.get_business_profile(obj)
        return bp.business_name if bp else None


    # -------------------------
    # ADDRESS (COMBINED)
    # -------------------------
    def get_address(self, obj):
        user = obj.user
        bp = self.get_business_profile(obj)

        return {
            "user_address": user.address,
            "user_latitude": user.latitude,
            "user_longitude": user.longitude,
            "business_latitude": bp.latitude if bp else None,
            "business_longitude": bp.longitude if bp else None,
        }



class LandscaperProfileSerializer(serializers.ModelSerializer):

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    plan = serializers.SerializerMethodField()
    name = serializers.CharField(source="user.name")
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    services = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()
    worker_count = serializers.SerializerMethodField()

    already_sent = serializers.SerializerMethodField()
    connection_request_id = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    # business_name = serializers.SerializerMethodField()
    # business_email = serializers.SerializerMethodField()
    # business_phone = serializers.SerializerMethodField()
    is_connected = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProfile
        fields = [
            "id",
            "user_id",
            "email",
            "plan",
            "name",
            "phone",
            # "business_name",
            # "business_email",
            # "business_phone",
            "latitude",
            "longitude",
            "address",
            "image",
            "working_hours",
            "services",
            "worker_count",
            "already_sent",
            "is_connected",
            "connection_request_id",
            "average_rating",
            "total_reviews",
            "reviews",
        ]

    # -------------------------
    # PLAN (OPTIMIZED)
    # -------------------------
    def get_plan(self, obj):
        subscription = Subscription.objects.filter(
            user=obj.user,
            is_active=True,
            status=SubscriptionStatus.ACTIVE
        ).select_related("plan").first()
        return subscription.plan.name.lower() if subscription else "free"

    # -------------------------
    # NAME / PHONE (NO DB CALL)
    # -------------------------
    def get_name(self, obj):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=obj.user)
        return profile.name

    def get_phone(self, obj):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=obj.user)
        return profile.phone

    def get_image(self, obj):
        return obj.profile_image.url if getattr(obj, "profile_image", None) else None

    # -------------------------
    # WORKING HOURS (FROM PREFETCH)
    # -------------------------
    def get_working_hours(self, obj):
        hours = getattr(obj, "pref_working_hours", [])
        return WorkingHoursSerializer(hours[:7], many=True).data

    # -------------------------
    # SERVICES (FROM PREFETCH)
    # -------------------------
    def get_services(self, obj):
        return [
            {
                "id": s.id,
                "name": s.name,
                "pricing_type": s.pricing_type,
                "price": float(s.base_price) if s.pricing_type == "fixed"
                else float(s.min_price or 0),
            }
            for s in getattr(obj, "pref_services", [])[:5]
        ]

    # -------------------------
    # REVIEWS (FROM PREFETCH)
    # -------------------------
    def get_reviews(self, obj):
        reviews = getattr(obj.user, "pref_reviews", [])
        return LandscaperReviewSerializer(reviews[:3], many=True).data

    # -------------------------
    # RATINGS (NO DB QUERY)
    # -------------------------
    def get_average_rating(self, obj):
        reviews = getattr(obj.user, "pref_reviews", [])
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_total_reviews(self, obj):
        return len(getattr(obj.user, "pref_reviews", []))

    # def get_business_name(self, obj):
    #     business = getattr(obj.user, "landscaper_profile", None)
    #     return business.business_name if business else None


    # def get_business_email(self, obj):
    #     business = getattr(obj.user, "landscaper_profile", None)
    #     return business.business_email if business else None


    # def get_business_phone(self, obj):
    #     business = getattr(obj.user, "landscaper_profile", None)
    #     return business.business_phone if business else None

    def get_worker_count(self, obj):
        bp = getattr(obj.user, "landscaper_profile", None)

        if not bp:
            return 0

        return bp.team_invitations.filter(
            status=InvitationStatus.ACCEPTED
        ).count()

    # -------------------------
    # CONNECTION LOGIC (KEEP BUT OPTIMIZED LATER)
    # -------------------------
    def get_already_sent(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user)
        ).exists()

    def get_is_connected(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user),
            is_accepted=True
        ).exists()

    def get_connection_request_id(self, obj):
        request = self.context.get("request")
        if not request:
            return None

        conn = ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user)
        ).first()

        return conn.id if conn else None

    # -------------------------
    # ADDRESS (❌ FIXED - REMOVED SLOW GEOCODING)
    # -------------------------
    def get_address(self, obj):
        return getattr(obj, "address", None)


# # serializers.py for client
# class ClientProfileSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(read_only=True)
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     name = serializers.CharField(source="user.name")
#     email = serializers.EmailField(source="user.email", read_only=True)
#     phone = serializers.CharField(source="user.phone", read_only=True)
#     image = serializers.ImageField(required=False, allow_null=True)
#     latitude = serializers.DecimalField(source="user.latitude", max_digits=20, decimal_places=14, read_only=True)
#     longitude = serializers.DecimalField(source="user.longitude", max_digits=20, decimal_places=14, read_only=True)
#     address = serializers.SerializerMethodField()


#     # services = serializers.SerializerMethodField()
#     properties = serializers.SerializerMethodField()
#     # total_service_price = serializers.SerializerMethodField()
#     already_sent = serializers.SerializerMethodField()  
#     connection_request_id = serializers.SerializerMethodField()
  
#     class Meta:
#         model = ClientProfile
#         fields = [   # ✅ MUST be inside Meta
#             "id",
#             "user_id",
#             "email",
#             "name",
#             "phone",
#             "latitude",
#             "longitude",
#             "address",
#             "image",
#             "properties",
#             "already_sent",
#             "connection_request_id",
#         ]


#     def get_address(self, obj):
#         # Get address from related User model
#         return getattr(obj.user, "address", None)



#     def get_properties(self, obj):
#         properties = Property.objects.filter(owner=obj.user)
#         return [
#             {
#                 "address": p.address,
#                 "latitude": p.latitude,
#                 "longitude": p.longitude,
#                 "property_size": p.property_size,
#                 "cut_height_inches": p.cut_height_inches,
#                 "grass_types": p.grass_types,
#                 "notes": p.notes,
#                 "images": p.images,
#             }
#             for p in properties
#         ]

#     def get_already_sent(self, obj):
#             """
#             Returns True if a connection request already exists
#             between logged-in user and this client
#             """
#             request = self.context.get("request")
#             if not request or not request.user.is_authenticated:
#                 return False

#             return ConnectionRequest.objects.filter(
#                 Q(sender=request.user, receiver=obj.user) |
#                 Q(sender=obj.user, receiver=request.user)
#             ).exists()
    

#     def get_connection_request_id(self, obj):
            
#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return None

#         connection = ConnectionRequest.objects.filter(
#             Q(sender=request.user, receiver=obj.user) |
#             Q(sender=obj.user, receiver=request.user),
#             is_accepted__isnull=True
#         ).first()

#         return connection.id if connection else None




class ClientProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    # ✅ WRITE FIELD (used for update)
    name = serializers.CharField(required=False)

    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    image = serializers.ImageField(required=False, allow_null=True)

    latitude = serializers.DecimalField(
        source="user.latitude",
        max_digits=20,
        decimal_places=14,
        read_only=True
    )
    longitude = serializers.DecimalField(
        source="user.longitude",
        max_digits=20,
        decimal_places=14,
        read_only=True
    )

    address = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    already_sent = serializers.SerializerMethodField()
    connection_request_id = serializers.SerializerMethodField()
    is_connected = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "user_id",
            "email",
            "name",   # ✅ single name field
            "phone",
            "latitude",
            "longitude",
            "address",
            "image",
            "properties",
            "already_sent",
            "is_connected",
            "connection_request_id",
        ]

    # =========================
    # ✅ UPDATE FIX
    # =========================
    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)

        if name is not None:
            instance.user.name = name
            instance.user.save()

        return super().update(instance, validated_data)

    # =========================
    # ✅ OUTPUT FIX (VERY IMPORTANT)
    # =========================
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 🔥 override name in response
        data["name"] = instance.user.name

        return data

    # =========================
    # ADDRESS
    # =========================
    def get_address(self, obj):
        return getattr(obj.user, "address", None)

    # =========================
    # PROPERTIES
    # =========================
    def get_properties(self, obj):
        properties = Property.objects.filter(owner=obj.user)

        return [
            {
                "id": p.id,
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

    # =========================
    # CONNECTION HELPERS
    # =========================
    def _get_connection(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        return ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user)
        ).first()

    def get_already_sent(self, obj):
        return self._get_connection(obj) is not None

    def get_connection_request_id(self, obj):
        connection = self._get_connection(obj)
        return connection.id if connection else None

    def get_is_connected(self, obj):
        connection = self._get_connection(obj)
        return connection.is_accepted is True if connection else False


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
    connected_profile = serializers.DictField()  
    created_at = serializers.DateTimeField()


# atggole
from rest_framework import serializers
from .models import LandscaperProfilies, ClientProfile

class LandscaperReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandscaperProfilies
        fields = ["job_reminder", "calendar_sync"]

class ClientReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ["service_reminder", "calendar_sync"]



# extern client serializers
from rest_framework import serializers
from profiles.models import ExternalClient


class ExternalClientSerializer(serializers.ModelSerializer):
    landscaper_id = serializers.IntegerField(source="landscaper.id", read_only=True)
    landscaper_business_name = serializers.CharField(
        source="landscaper.business_name",
        read_only=True
    )

    class Meta:
        model = ExternalClient
        fields = [
            "id",
            "landscaper_id",
            "landscaper_business_name",
            "name",
            "email",
            "phone",
            "company_name",
            "address",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "landscaper_id",
            "landscaper_business_name",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        phone = attrs.get("phone")

        if not email and not phone:
            raise serializers.ValidationError(
                "At least one contact field is required: email or phone."
            )

        return attrs