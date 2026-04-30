


from rest_framework import serializers
from landscapers.models import BusinessProfile, WorkingHours
from landscapers.models import Service
from profiles.models import LandscaperProfilies
from reviews.models import LandscaperReview
from reviews.serializers import LandscaperReviewSerializer

class PublicServiceSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "pricing_type",
            "price",
            "is_pinned",
        ]

    def get_price(self, obj):
        # Handle pricing logic cleanly
        if obj.pricing_type == Service.PricingType.FIXED:
            return float(obj.base_price) if obj.base_price else None

        if obj.pricing_type == Service.PricingType.REQUEST:
            return {
                "type": "request",
                "min_price": float(obj.min_price) if obj.min_price else None
            }

        return None

        
class WeeklyAvailabilitySerializer(serializers.ModelSerializer):
    day = serializers.CharField(source="get_day_display")

    class Meta:
        model = WorkingHours
        fields = ["day", "start_time", "end_time"]

class PublicLandscaperSerializer(serializers.ModelSerializer):
    # From User
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    address = serializers.CharField(source="user.address", read_only=True)
    reviews = serializers.SerializerMethodField()

    # Custom fields
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    services = serializers.SerializerMethodField()
    weekly_schedule = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProfile
        fields = [
            "user_id",
            "image",
            "name",
            "email",
            "phone",
            "address",
            "business_name",
            "reviews",
            "latitude",
            "longitude",
            "services",
            "weekly_schedule",
        ]

    # -----------------------
    # SAFE BASIC PROFILE
    # -----------------------
    def get_basic_profile(self, obj):
        return getattr(obj.user, "landscaperprofilies", None)

    # -----------------------
    # PHONE
    # -----------------------
    def get_phone(self, obj):
        profile = self.get_basic_profile(obj)
        return getattr(profile, "phone", None)

    # -----------------------
    # IMAGE
    # -----------------------
    def get_image(self, obj):
        profile = self.get_basic_profile(obj)
        if profile and getattr(profile, "image", None):
            return profile.image.url
        return None

    def get_reviews(self, obj):
        reviews = LandscaperReview.objects.filter(
            landscaper=obj.user
        ).select_related("client").order_by("-created_at")

        return LandscaperReviewSerializer(reviews, many=True).data

    # -----------------------
    # BUSINESS NAME (from BusinessProfile)
    # -----------------------
    def get_business_name(self, obj):
        return getattr(obj, "business_name", None)

    # -----------------------
    # LATITUDE
    # -----------------------
    def get_latitude(self, obj):
        return getattr(obj, "latitude", None)

    # -----------------------
    # LONGITUDE
    # -----------------------
    def get_longitude(self, obj):
        return getattr(obj, "longitude", None)

    # -----------------------
    # SERVICES
    # -----------------------
    def get_services(self, obj):
        services = Service.objects.filter(business=obj, is_active=True)

        result = []

        for s in services:
            # Handle pricing correctly
            if s.pricing_type == "fixed":
                price = float(s.base_price) if s.base_price else 0
            else:  # request
                price = float(s.min_price) if s.min_price else 0

            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "pricing_type": s.pricing_type,
                "price": price,
            })

        return result

    # -----------------------
    # WORKING HOURS (SAFE)
    # -----------------------
    def get_weekly_schedule(self, obj):
        hours = obj.working_hours.all()
        return WeeklyAvailabilitySerializer(hours, many=True).data