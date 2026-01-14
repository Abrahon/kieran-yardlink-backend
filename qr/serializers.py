from rest_framework import serializers
from landscapers.models import LandscaperProfile, WorkingHours
from services.models import Service


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
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    image = serializers.SerializerMethodField()

    services = PublicServiceSerializer(
        many=True,
        read_only=True
    )

    weekly_schedule = WeeklyAvailabilitySerializer(
        source="weekly_availability",
        many=True,
        read_only=True
    )

    class Meta:
        model = LandscaperProfile
        fields = [
            "image",
            "name",
            "email",
            "company_name",
            "phone",
            "address",
            "latitude",
            "longitude",
            "services",
            "weekly_schedule",
        ]

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
