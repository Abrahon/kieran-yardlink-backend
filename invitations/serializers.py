# invitations/serializers.py
from rest_framework import serializers
from .models import TeamInvitation


class SendInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AcceptInvitationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

class InvitationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = (
            "id",
            "email",
            "status",
            "expires_at",
            "created_at",
            "token",
        )


# from rest_framework import serializers
# from .models import WorkerProfile


# class WorkerProfileSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source="user.email", read_only=True)
#     name = serializers.CharField(source="user.get_full_name", read_only=True)

#     class Meta:
#         model = WorkerProfile
#         fields = [
#             "id",
#             "email",
#             "name",
#             "is_blocked",
#             "created_at",
#         ]

