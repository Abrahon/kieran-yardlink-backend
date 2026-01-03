from rest_framework import serializers
from landscapers.models import LandscaperProfile

class PublicLandscaperSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = LandscaperProfile
        fields = [
            "name",
            "email",
            "company_name",
            "phone",
            "experience_years",
            "rating",
        ]
