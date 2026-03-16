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
# from jobs .models import Job
# from subscr.models import Plan
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

            return obj.image.url
              # return full Cloudinary URL
        return None



# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     plan = serializers.SerializerMethodField()

#     # Model fields for writable
#     name = serializers.CharField(required=False)
#     phone = serializers.CharField(required=False)
#     image = serializers.ImageField(required=False, allow_null=True)

#     # Read-only/derived fields
#     # Fix latitude & longitude to fallback if null
#     latitude = serializers.SerializerMethodField()

#     longitude = serializers.SerializerMethodField()
    
#     business_name = serializers.SerializerMethodField()
#     address = serializers.SerializerMethodField()

#     upcoming_jobs = serializers.SerializerMethodField()
#     completed_jobs = serializers.SerializerMethodField() 
   
#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()
#     already_sent = serializers.SerializerMethodField() 
#     connection_request_id = serializers.SerializerMethodField()
#     average_rating = serializers.SerializerMethodField()
#     total_reviews = serializers.SerializerMethodField()
#     reviews = serializers.SerializerMethodField()

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id",
#             "user_id",
#             "email",
#             "plan",
#             "name",
#             "phone",
#             "latitude",
#             "longitude",
#             "address",
#             "image",
#             "business_name",
#             "working_hours",
#             "services",
#             "upcoming_jobs",
#             "completed_jobs",
#             "already_sent",
#             "connection_request_id",
#             "average_rating",
#             "total_reviews",
#             "reviews",
#         ]

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data["image"] = instance.image.url if instance.image else None
#         return data

#     def get_plan(self, obj):
#         """
#         Plan is derived from ACTIVE subscription (Stripe-controlled)
#         """
#         subscription = (
#             Subscription.objects
#             .filter(
#                 user=obj.user,
#                 is_active=True,
#                 status=SubscriptionStatus.ACTIVE
#             )
#             .select_related("plan")
#             .first()
#         )

#         if subscription:
#             return subscription.plan.name.lower()  # e.g. "basic", "pro"

#         return "free"


#     def get_working_hours(self, obj):
#         try:
#             # Map your business profile to the landscaper
#             profile = BusinessProfile.objects.get(user=obj.user)
#         except BusinessProfile.DoesNotExist:
#             return []

#         hours = WorkingHours.objects.filter(landscaper=profile).order_by("day")
#         return WHSerializer(hours, many=True).data
    
    
#     def get_business_profile(self, obj):
#         try:
#             return BusinessProfile.objects.get(user=obj.user)
#         except BusinessProfile.DoesNotExist:
#             return None
    
#     def get_business_name(self, obj):
#         business = self.get_business_profile(obj)
#         return business.business_name if business else None
    
#         # lat and lng from business profile 

#     def get_latitude(self, obj):
#         business = getattr(obj.user, "landscaper_profile", None)  # your business model
#         return float(business.latitude) if business and business.latitude else None

#     def get_longitude(self, obj):
#         business = getattr(obj.user, "landscaper_profile", None)
#         return float(business.longitude) if business and business.longitude else None

#     def get_address(self, obj):
#         business = getattr(obj.user, "landscaper_profile", None)
#         if business and business.latitude and business.longitude:
#             # Use geopy or any reverse geocoding method
#             from geopy.geocoders import Nominatim
#             geolocator = Nominatim(user_agent="yardlink_app")
#             try:
#                 location = geolocator.reverse(f"{business.latitude}, {business.longitude}")
#                 return location.address if location else None
#             except:
#                 return None
#         return None

#     def get_services(self, obj):
#         """
#         Return all services for the landscaper in a safe, DRF-friendly format.
#         """
#         services = Service.objects.filter(landscaper=obj.user)
#         result = []

#         for s in services:
#             result.append({
#                 "id": s.id,
#                 "category": s.category,  # "standard" or "custom"
#                 "standard_service": s.standard_service or "",
#                 "description": s.description or "",
#                 "price": float(s.price) if s.price else 0,
#                 "time": float(s.time) if s.time else 0,
#                 "rate_type": s.rate_type or "",
#                 "latitude": float(s.latitude) if s.latitude else None,
#                 "longitude": float(s.longitude) if s.longitude else None,
#                 "is_active": s.is_active,
#                 "created_at": s.created_at,
#                 "updated_at": s.updated_at,
#             })

#         return result

#     def get_upcoming_jobs(self, obj):
#         jobs = ServiceSchedule.objects.filter(
#             landscaper=obj,
#             is_completed=False,
#             scheduled_date__gte=timezone.now().date()
#         ).order_by("scheduled_date", "scheduled_time")
#         return JobSerializer(jobs, many=True).data

#     def get_completed_jobs(self, obj):
#         jobs = ServiceSchedule.objects.filter(
#             landscaper=obj,
#             is_completed=True
#         ).order_by("-completed_at")
#         return JobSerializer(jobs, many=True).data

#     # Connection request helpers
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


#     def get_already_sent(self, obj):
#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return False
#         return ConnectionRequest.objects.filter(
#             Q(sender=request.user, receiver=obj.user) |
#             Q(sender=obj.user, receiver=request.user)
#         ).exists()

#     def get_average_rating(self, obj):
#         avg = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).aggregate(avg=Avg("rating"))["avg"] or 0
#         return round(avg, 1)

#     def get_total_reviews(self, obj):
#         return LandscaperReview.objects.filter(landscaper=obj.user).count()

#     def get_reviews(self, obj):
#         reviews = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).select_related("client").order_by("-created_at")
#         return LandscaperReviewSerializer(reviews, many=True).data

from rest_framework import serializers
from django.db.models import Avg
from django.utils import timezone
from landscapers.models import BusinessProfile
from subscriptions.models import Subscription, SubscriptionStatus
from jobs.models import Job



class LandscaperPersonalProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    profile_image = serializers.ImageField(source="image", required=False, allow_null=True)

    class Meta:
        model = LandscaperProfilies
        fields = ["email", "name", "phone", "profile_image"]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.phone = validated_data.get("phone", instance.phone)

        if "image" in validated_data:
            instance.image = validated_data["image"]

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["profile_image"] = instance.image.url if instance.image else None
        return data



# class LandscaperProfileSerializer(serializers.ModelSerializer):
#     # Read-only user info
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     plan = serializers.SerializerMethodField()

#     # Personal info
#     name = serializers.CharField(required=False)
#     phone = serializers.CharField(required=False)

#     # Business info
#     image = serializers.ImageField(source="profile_image", required=False, allow_null=True)
#     business_name = serializers.CharField(read_only=True)
#     latitude = serializers.FloatField(required=False, allow_null=True)
#     longitude = serializers.FloatField(required=False, allow_null=True)
#     address = serializers.SerializerMethodField()

#     # Related info
#     services = serializers.SerializerMethodField()
#     upcoming_jobs = serializers.SerializerMethodField()
#     completed_jobs = serializers.SerializerMethodField()
#     average_rating = serializers.SerializerMethodField()
#     total_reviews = serializers.SerializerMethodField()
#     reviews = serializers.SerializerMethodField()

#     class Meta:
#         model = BusinessProfile
#         fields = [
#             "id", "user_id", "email", "plan",
#             "name", "phone",
#             "latitude", "longitude", "business_name", "address", "image",
#             "services", "upcoming_jobs", "completed_jobs",
#             "average_rating", "total_reviews", "reviews",
#         ]

#     # --------------------------
#     # SerializerMethodField methods
#     # --------------------------
#     def get_plan(self, obj):
#         subscription = Subscription.objects.filter(
#             user=obj.user, is_active=True, status=SubscriptionStatus.ACTIVE
#         ).select_related("plan").first()
#         return subscription.plan.name.lower() if subscription else "free"

#     def get_address(self, obj):
#         if obj.latitude and obj.longitude:
#             geolocator = Nominatim(user_agent="yardlink_app")
#             try:
#                 location = geolocator.reverse(f"{obj.latitude}, {obj.longitude}")
#                 return location.address if location else None
#             except:
#                 return None
#         return None

#     def get_services(self, obj):
#         services = Service.objects.filter(business=obj)
#         return [
#             {
#                 "id": s.id,
#                 "name": s.name,
#                 "description": s.description,
#                 "price": float(s.base_price) if s.base_price else 0,
#                 "pricing_type": s.pricing_type,
#                 "min_price": float(s.min_price) if s.min_price else 0,
#                 "latitude": float(s.latitude) if s.latitude else None,
#                 "longitude": float(s.longitude) if s.longitude else None,
#                 "is_active": s.is_active,
#                 "created_at": s.created_at,
#                 "updated_at": s.updated_at,
#             }
#             for s in services
#         ]

#     def get_upcoming_jobs(self, obj):
#         jobs = Job.objects.filter(
#             landscaper=obj.user, status=Job.Status.UPCOMING, is_active=True
#         ).order_by("scheduled_date", "scheduled_time")
#         return JobSerializer(jobs, many=True).data

#     def get_completed_jobs(self, obj):
#         jobs = Job.objects.filter(
#             landscaper=obj.user, status=Job.Status.COMPLETED, is_active=True
#         ).order_by("-completed_at")
#         return JobSerializer(jobs, many=True).data

#     def get_average_rating(self, obj):
#         avg = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).aggregate(avg=Avg("rating"))["avg"] or 0
#         return round(avg, 1)

#     def get_total_reviews(self, obj):
#         return LandscaperReview.objects.filter(landscaper=obj.user).count()

#     def get_reviews(self, obj):
#         reviews = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).select_related("client").order_by("-created_at")
#         return LandscaperReviewSerializer(reviews, many=True).data

#     # --------------------------
#     # Override to_representation for image URL
#     # --------------------------
#     # --------------------------
#     # Override to_representation for image URL
#     # --------------------------
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data["image"] = instance.profile_image.url if instance.profile_image else None

#         profile, _ = LandscaperProfilies.objects.get_or_create(user=instance.user)
#         data["name"] = profile.name
#         data["phone"] = profile.phone

#         return data

#     # --------------------------
#     # Override update to handle personal info + business profile
#     # --------------------------
#     def update(self, instance, validated_data):
#         # remove personal fields from validated_data
#         name = validated_data.pop("name", None)
#         phone = validated_data.pop("phone", None)

#         # update BusinessProfile fields
#         instance.latitude = validated_data.get("latitude", instance.latitude)
#         instance.longitude = validated_data.get("longitude", instance.longitude)

#         if "profile_image" in validated_data:
#             instance.profile_image = validated_data["profile_image"]

#         instance.save()

#         # update/create LandscaperProfilies
#         profile, _ = LandscaperProfilies.objects.get_or_create(user=instance.user)

#         if name is not None:
#             profile.name = name
#         if phone is not None:
#             profile.phone = phone

#         profile.save()

#         return instance


from rest_framework import serializers
from django.db.models import Avg
from geopy.geocoders import Nominatim
from landscapers.serializers import WorkingHoursSerializer


# from subscriptions.models import Subscription, SubscriptionStatus

class LandscaperProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    plan = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()

    already_sent = serializers.SerializerMethodField()
    connection_request_id = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()


    class Meta:
        model = BusinessProfile
        fields = [
            "id",
            "user_id",
            "email",
            "plan",
            "name",
            "phone",
            "business_name",
            "business_email",
            "business_phone",
            "latitude",
            "longitude",
            "address",
            "image",
            "working_hours",
            "services",
            "already_sent",
            "connection_request_id",
            "average_rating",
            "total_reviews",
            "reviews",
        ]

    def get_plan(self, obj):
        subscription = Subscription.objects.filter(
            user=obj.user,
            is_active=True,
            status=SubscriptionStatus.ACTIVE
        ).select_related("plan").first()
        return subscription.plan.name.lower() if subscription else "free"

    def get_name(self, obj):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=obj.user)
        return profile.name

    def get_phone(self, obj):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=obj.user)
        return profile.phone

    def get_image(self, obj):
        return obj.profile_image.url if obj.profile_image else None
    
    def get_working_hours(self, obj):
        hours = obj.working_hours.filter(is_active=True)
        return WorkingHoursSerializer(hours, many=True).data


    def get_services(self, obj):
        services = Service.objects.filter(business=obj)
        return [
            {
                "id": s.id,
                "name": s.name,
            }
            for s in services
        ]

    def get_already_sent(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return ConnectionRequest.objects.filter(
            sender=request.user,
            receiver=obj.user,
            is_accepted=False
        ).exists()


    def get_connection_request_id(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        connection = ConnectionRequest.objects.filter(
            sender=request.user,
            receiver=obj.user,
            is_accepted=False
        ).first()

        return connection.id if connection else None

    def get_average_rating(self, obj):
        avg = LandscaperReview.objects.filter(
            landscaper=obj.user
        ).aggregate(avg=Avg("rating"))["avg"] or 0
        return round(avg, 1)

    def get_total_reviews(self, obj):
        return LandscaperReview.objects.filter(
            landscaper=obj.user
        ).count()

    def get_reviews(self, obj):
        reviews = LandscaperReview.objects.filter(
            landscaper=obj.user
        ).select_related("client").order_by("-created_at")
        return LandscaperReviewSerializer(reviews, many=True).data

    def get_address(self, obj):
        if obj.latitude and obj.longitude:
            geolocator = Nominatim(user_agent="yardlink_app")
            try:
                location = geolocator.reverse(f"{obj.latitude}, {obj.longitude}")
                return location.address if location else None
            except Exception:
                return None
        return None


# serializers.py for client
class ClientProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    latitude = serializers.DecimalField(source="user.latitude", max_digits=20, decimal_places=14, read_only=True)
    longitude = serializers.DecimalField(source="user.longitude", max_digits=20, decimal_places=14, read_only=True)
    address = serializers.SerializerMethodField()


    services = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    total_service_price = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField()  
    connection_request_id = serializers.SerializerMethodField()
  


    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "user_id",
            "email",
            "name",
            "phone",
            "latitude",
            "longitude",
            "address",
            "image",
            "services", 
            "total_service_price",
            "properties",
            "already_sent",
            "connection_request_id",
        ]


    def get_address(self, obj):
        # Get address from related User model
        return getattr(obj.user, "address", None)


    def get_services(self, obj):
        """
        Return all standard services to the client.
        """
        services_qs = ClientService.objects.filter(is_standard=True) 

        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "price": str(s.price) if s.price else None,
                "square_feet": float(s.square_feet) if s.square_feet else None,
                "is_standard": s.is_standard,
                "image": s.image.url if s.image else None,
            }
            for s in services_qs
        ]



    #  Add this method to calculate total service price
    def get_total_service_price(self, obj):
        services_qs = ClientService.objects.filter(is_standard=True)
        return sum(float(service.price or 0) for service in services_qs)


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