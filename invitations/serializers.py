# invitations/serializers.py
from rest_framework import serializers
from .models import TeamInvitation


class SendInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AcceptInvitationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=100)
