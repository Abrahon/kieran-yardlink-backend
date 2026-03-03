


from rest_framework import serializers
from landscapers.models import BusinessProfile, WorkingHours
from services.models import Service
from profiles.models import LandscaperProfilies

class PublicServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service  # or LandscaperService if exists
        fields = ["id", "standard_service", "price", "category"]
        
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

    # From Profiles
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    # Related objects
    services = serializers.SerializerMethodField()
    weekly_schedule = WeeklyAvailabilitySerializer(
        source="working_hours",
        many=True,
        read_only=True
    )

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
            "latitude",
            "longitude",
            "services",
            "weekly_schedule",
        ]

    def get_basic_profile(self, obj):
        try:
            return LandscaperProfilies.objects.get(user=obj.user)
        except LandscaperProfilies.DoesNotExist:
            return None

    def get_business_profile(self, obj):
        try:
            return LandscaperProfile.objects.get(user=obj.user)
        except LandscaperProfile.DoesNotExist:
            return None

    def get_phone(self, obj):
        profile = self.get_basic_profile(obj)
        return profile.phone if profile else None

    def get_image(self, obj):
        profile = self.get_basic_profile(obj)
        return profile.image.url if profile and profile.image else None

    def get_business_name(self, obj):
        profile = self.get_business_profile(obj)
        return profile.business_name if profile else None

    def get_latitude(self, obj):
        profile = self.get_business_profile(obj)
        return float(profile.latitude) if profile and profile.latitude else None

    def get_longitude(self, obj):
        profile = self.get_business_profile(obj)
        return float(profile.longitude) if profile and profile.longitude else None

    def get_services(self, obj):
        # obj is LandscaperProfile
        services = Service.objects.filter(landscaper=obj.user)  # Link to User
        return [
            {
                "id": s.id,
                "category": s.category,
                "standard_service": getattr(s, "standard_service", None),
                "custom_service": getattr(s, "custom_service", None),
                "description": s.description,
                "price": float(s.price),
                "per_square_feet": float(getattr(s, "per_square_feet", 0)),
                "latitude": float(s.latitude) if s.latitude else None,
                "longitude": float(s.longitude) if s.longitude else None,
                "add_ons": getattr(s, "add_ons", None),
            }
            for s in services
        ]