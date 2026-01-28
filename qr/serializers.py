from rest_framework import serializers
from landscapers.models import LandscaperProfile, WorkingHours
from services.models import Service
from profiles.models import LandscaperProfilies


class PublicServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "price"]


class WeeklyAvailabilitySerializer(serializers.ModelSerializer):
    day = serializers.CharField(source="get_day_of_week_display")

    class Meta:
        model = WorkingHours
        fields = ["day", "start_time", "end_time"]


class PublicLandscaperSerializer(serializers.ModelSerializer):
    # from accounts.User
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    address = serializers.CharField(source="user.address", read_only=True)

    # from profiles app
    phone = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    services = PublicServiceSerializer(many=True, read_only=True)

    weekly_schedule = WeeklyAvailabilitySerializer(
        source="weekly_availability",
        many=True,
        read_only=True
    )

    class Meta:
        model = LandscaperProfile
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
        
    # Helper methods

    def get_profile(self, obj):
        """
        Fetch LandscaperProfilies safely
        """
        try:
            return LandscaperProfilies.objects.get(user=obj.user)
        except LandscaperProfilies.DoesNotExist:
            return None

    def get_phone(self, obj):
        profile = self.get_profile(obj)
        return profile.phone if profile else None

    def get_image(self, obj):
        profile = self.get_profile(obj)
        if profile and profile.image:
            return profile.image.url
        return None
