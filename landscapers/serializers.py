from rest_framework import serializers
from .models import LandscaperProfile
from services.models import Service
from services.serializers import ServiceSerializer

class LandscaperProfileSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True)
    profile_url = serializers.SerializerMethodField()  # to return Cloudinary URL

    class Meta:
        model = LandscaperProfile
        fields = [
            "business_name",
            "business_email",
            "business_phone",
            "service_address",
            "latitude",
            "longitude",
            "services",
            "profile",       # raw Cloudinary field
            "profile_url",   # URL for frontend
        ]

    def get_profile_url(self, obj):
        if obj.profile:
            return obj.profile.url
        return None

    def create(self, validated_data):
        services_data = validated_data.pop("services")
        image = validated_data.pop("profile", None)  # handle image

        user = self.context["request"].user

        profile = LandscaperProfile.objects.create(
            user=user,
            is_profile_completed=True,
            **validated_data
        )

        if image:
            profile.profile = image  # Cloudinary handles upload automatically
            profile.save()

        for service in services_data:
            Service.objects.create(
                landscaper=profile,
                **service
            )

        return profile


# working hours serializers

# landscapers/serializers.py
from rest_framework import serializers
from .models import WorkingHours, DAYS_OF_WEEK

class WorkingHoursSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']
