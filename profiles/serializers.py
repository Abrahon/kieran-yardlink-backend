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
from landscapers.models import WorkingHours, LandscaperProfile
from landscapers.serializers import WorkingHoursSerializer as WHSerializer
from landscapers.models import WorkingHours, LandscaperProfile, Service
from services.models import ClientService 
from connections.models import ConnectionRequest
from subscriptions.models import Plan,Subscription
from subscriptions.enums import SubscriptionStatus
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
#     name = serializers.CharField(source="user.name", read_only=True)
#     email = serializers.EmailField(source="user.email", read_only=True)
#     phone = serializers.CharField(source="user.phone", read_only=True)
#     image = serializers.ImageField(required=False, allow_null=True)
#     latitude = serializers.DecimalField(source="user.latitude", max_digits=20, decimal_places=14, read_only=True)
#     longitude = serializers.DecimalField(source="user.longitude", max_digits=20, decimal_places=14, read_only=True)
   


#     business_name = serializers.CharField(
#         source="user.landscaper_profile.business_name",
#         read_only=True
#     )

#     working_hours = serializers.SerializerMethodField()
#     services = serializers.SerializerMethodField()
#     already_sent = serializers.SerializerMethodField() 
#     connection_request_id = serializers.SerializerMethodField()
#     average_rating = serializers.SerializerMethodField()
#     total_reviews = serializers.SerializerMethodField()
#     reviews = serializers.SerializerMethodField()  # optional: full review list

#     class Meta:
#         model = LandscaperProfilies
#         fields = [
#             "id",
#             "user_id",
#             "email",
#             "name",
#             "phone",
#             "latitude",
#             "longitude",
#             "image",
#             "business_name",
#             "working_hours",
#             "services",
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
#     def get_connection_request_id(self, obj):

#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return None

#         connection = ConnectionRequest.objects.filter(
#             Q(sender=request.user, receiver=obj.user) |
#             Q(sender=obj.user, receiver=request.user),
#             is_accepted__isnull=True  # pending only
#         ).first()

#         return connection.id if connection else None


#     def get_already_sent(self, obj):
#         """
#         True if a connection request already exists
#         between logged-in user and this landscaper
#         """
#         request = self.context.get("request")
#         if not request or not request.user.is_authenticated:
#             return False

#         return ConnectionRequest.objects.filter(
#             Q(sender=request.user, receiver=obj.user) |
#             Q(sender=obj.user, receiver=request.user)
#         ).exists()

#     # reviews
#     def get_average_rating(self, obj):
#         avg = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).aggregate(avg=Avg("rating"))["avg"] or 0
#         return round(avg, 1)

#     def get_total_reviews(self, obj):
#         return LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).count()

#     def get_reviews(self, obj):
#         reviews = LandscaperReview.objects.filter(
#             landscaper=obj.user
#         ).select_related("client").order_by("-created_at")
#         return LandscaperReviewSerializer(reviews, many=True).data


class LandscaperProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    plan = serializers.SerializerMethodField()

    # Model fields for writable
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    image = serializers.ImageField(required=False, allow_null=True)

    # Read-only/derived fields
    # Fix latitude & longitude to fallback if null
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField() 
   
    working_hours = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField() 
    connection_request_id = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = LandscaperProfilies
        fields = [
            "id",
            "user_id",
            "email",
            "plan",
            "name",
            "phone",
            "latitude",
            "longitude",
            "image",
            "business_name",
            "working_hours",
            "services",
            "already_sent",
            "connection_request_id",
            "average_rating",
            "total_reviews",
            "reviews",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["image"] = instance.image.url if instance.image else None
        return data

    def get_plan(self, obj):
        """
        Plan is derived from ACTIVE subscription (Stripe-controlled)
        """
        subscription = (
            Subscription.objects
            .filter(
                user=obj.user,
                is_active=True,
                status=SubscriptionStatus.ACTIVE
            )
            .select_related("plan")
            .first()
        )

        if subscription:
            return subscription.plan.name.lower()  # e.g. "basic", "pro"

        return "free"


    def get_working_hours(self, obj):

        try:
            # Map your business profile to the landscaper profile
            profile = LandscaperProfile.objects.get(user=obj.user)
        except LandscaperProfile.DoesNotExist:

            return []

        hours = WorkingHours.objects.filter(landscaper=profile).order_by("day")
        return WHSerializer(hours, many=True).data
    
    
    def get_business_profile(self, obj):
        """
        Return the corresponding LandscaperProfile (business model) for this user
        """
        try:
            return LandscaperProfile.objects.get(user=obj.user)
        except LandscaperProfile.DoesNotExist:
            return None
    
    def get_business_name(self, obj):
        business = self.get_business_profile(obj)
        return business.business_name if business else None
    
        # lat and lng from business profile 
    def get_latitude(self, obj):
        """
        Return latitude from the business profile if exists
        """
        business = self.get_business_profile(obj)
        if business:
            return business.latitude
        return None

    def get_longitude(self, obj):
        """
        Return longitude from the business profile if exists
        """
        business = self.get_business_profile(obj)
        if business:
            return business.longitude
        return None



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

    # Connection request helpers
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

    def get_already_sent(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return ConnectionRequest.objects.filter(
            Q(sender=request.user, receiver=obj.user) |
            Q(sender=obj.user, receiver=request.user)
        ).exists()

    def get_average_rating(self, obj):
        avg = LandscaperReview.objects.filter(
            landscaper=obj.user
        ).aggregate(avg=Avg("rating"))["avg"] or 0
        return round(avg, 1)

    def get_total_reviews(self, obj):
        return LandscaperReview.objects.filter(landscaper=obj.user).count()

    def get_reviews(self, obj):
        reviews = LandscaperReview.objects.filter(
            landscaper=obj.user
        ).select_related("client").order_by("-created_at")
        return LandscaperReviewSerializer(reviews, many=True).data



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
            "image",
            "services", 
            "total_service_price",
            "properties",
            "already_sent",
            "connection_request_id",
        ]



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
