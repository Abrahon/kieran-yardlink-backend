from rest_framework import serializers
from .models import ConnectionRequest

class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source="sender.email", read_only=True)
    receiver_email = serializers.EmailField(source="receiver.email", read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "sender_email",
            "receiver_email",
            "is_accepted",
            "created_at",
        ]
