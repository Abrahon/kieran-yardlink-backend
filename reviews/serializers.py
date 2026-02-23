from rest_framework import serializers
from .models import LandscaperReview


class LandscaperReviewSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source="client.id", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_email = serializers.EmailField(source="client.email", read_only=True)

    class Meta:
        model = LandscaperReview
        fields = [
            "id",
            "client_id",
            "client_name",
            "client_email",
            "rating",
            "comment",
            "created_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        landscaper = self.context.get("landscaper")

        if request.user == landscaper:
            raise serializers.ValidationError("You cannot review yourself")

        return attrs
