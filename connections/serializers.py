from rest_framework import serializers
from .models import ConnectionRequest
from accounts.models import User


class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_name = serializers.CharField(
        source="sender.get_full_name", read_only=True
    )

    receiver_id = serializers.IntegerField(source="receiver.id", read_only=True)
    receiver_name = serializers.CharField(
        source="receiver.get_full_name", read_only=True
    )

    status = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "sender_id",
            "sender_name",
            "receiver_id",
            "receiver_name",
            "status",
            "created_at",
        ]

    def get_status(self, obj):
        if obj.is_accepted is None:
            return "pending"
        return "accepted" if obj.is_accepted else "rejected"
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
        instance.is_accepted = validated_data["action"] == "accept"
        instance.save(update_fields=["is_accepted"])
        return instance
