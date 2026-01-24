# connections/serializers.py
from rest_framework import serializers
from .models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer
from landscapers.serializers import LandscaperProfileSerializer


class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "sender",
            "receiver",
            "is_accepted",
            "created_at",
            "sender_profile",
            "receiver_profile",
        ]
        read_only_fields = ["sender", "is_accepted", "created_at"]

    def get_sender_profile(self, obj):
        user = obj.sender

        if hasattr(user, "clientprofile"):
            return ClientProfileSerializer(user.clientprofile, context=self.context).data

        if hasattr(user, "landscaperprofilies"):
            return LandscaperProfileSerializer(
                user.landscaperprofilies, context=self.context
            ).data

        return None

    def get_receiver_profile(self, obj):
        user = obj.receiver

        if hasattr(user, "clientprofile"):
            return ClientProfileSerializer(user.clientprofile, context=self.context).data

        if hasattr(user, "landscaperprofilies"):
            return LandscaperProfileSerializer(
                user.landscaperprofilies, context=self.context
            ).data

        return None

class SendConnectionRequestSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()

    def validate_receiver_id(self, value):
        user = self.context["request"].user

        if user.id == value:
            raise serializers.ValidationError("You cannot send request to yourself.")

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")

        exists = ConnectionRequest.objects.filter(
            sender=user,
            receiver_id=value
        ).exists() or ConnectionRequest.objects.filter(
            sender_id=value,
            receiver=user
        ).exists()

        if exists:
            raise serializers.ValidationError("Request already exists.")

        return value

        


class RespondConnectionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject"])

    def update(self, instance, validated_data):
        # Update the ConnectionRequest instance
        instance.is_accepted = validated_data["action"] == "accept"
        instance.save(update_fields=["is_accepted"])
        return instance

