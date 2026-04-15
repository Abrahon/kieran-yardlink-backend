

# connections/serializers.py
from rest_framework import serializers
from .models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer
from landscapers.serializers import BusinessLandscaperProfileSerializer
from accounts.models import User
from rest_framework import serializers
from jobs.models import Job
from profiles.models import LandscaperProfilies
from rest_framework import serializers
from profiles.models import LandscaperProfilies, ClientProfile
from connections.models import ConnectionRequest
from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
from django.db.models import Q
from datetime import timedelta
from django.utils.timezone import now


# connections/serializers.py
from datetime import timedelta

from django.db.models import Q
from django.utils.timezone import now
from rest_framework import serializers

from accounts.models import User
from connections.models import ConnectionRequest
from profiles.models import LandscaperProfilies, ClientProfile
from profiles.serializers import ClientProfileSerializer
from landscapers.serializers import (
    BusinessLandscaperProfileSerializer,
    # LandscaperProfileSerializer,
)
from jobs.models import Job


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]


class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField()
    scheduled_job = serializers.SerializerMethodField()
    sent_since = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "is_accepted",
            "created_at",
            "sender_profile",
            "receiver_profile",
            "already_sent",
            "sent_since",
            "scheduled_job",
        ]

    def get_is_accepted(self, obj):
        return bool(obj.is_accepted)

    def _get_profile(self, user):
        """
        Return user profile depending on type:
        - landscaper business profile -> BusinessLandscaperProfileSerializer
        - landscaper basic profile -> fallback basic info
        - client profile -> ClientProfileSerializer
        """
        business_profile = getattr(user, "landscaper_profile", None)
        if business_profile:
            data = BusinessLandscaperProfileSerializer(
                business_profile,
                context=self.context
            ).data
            data["user_id"] = user.id
            data["email"] = user.email
            data["type"] = "landscaper_business"
            return data

        basic_profile = getattr(user, "landscaperprofilies", None)
        if basic_profile:
            return {
                "user_id": user.id,
                "name": basic_profile.name,
                "phone": basic_profile.phone,
                "image": basic_profile.image.url if basic_profile.image else None,
                "type": "landscaper_basic",
            }

        client_profile = getattr(user, "client_profile", None)
        if client_profile:
            data = ClientProfileSerializer(client_profile, context=self.context).data
            data["type"] = "client"
            return data

        return {
            "user_id": user.id,
            "email": user.email,
            "type": "unknown",
        }

    def get_sender_profile(self, obj):
        return self._get_profile(obj.sender)

    def get_receiver_profile(self, obj):
        return self._get_profile(obj.receiver)

    def get_sent_since(self, obj):
        delta = now() - obj.created_at

        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        return obj.created_at.strftime("%Y-%m-%d")

    def get_already_sent(self, obj):
        return ConnectionRequest.objects.filter(
            Q(sender=obj.sender, receiver=obj.receiver) |
            Q(sender=obj.receiver, receiver=obj.sender)
        ).exists()

    def get_scheduled_job(self, obj):
        """
        Return upcoming job only when connection is accepted.
        """
        if obj.is_accepted is not True:
            return None

        client_profile = None
        landscaper_profile = None

        # sender
        if hasattr(obj.sender, "client_profile"):
            client_profile = obj.sender.client_profile
        elif hasattr(obj.sender, "landscaperprofilies"):
            landscaper_profile = obj.sender.landscaperprofilies

        # receiver
        if hasattr(obj.receiver, "client_profile"):
            client_profile = obj.receiver.client_profile
        elif hasattr(obj.receiver, "landscaperprofilies"):
            landscaper_profile = obj.receiver.landscaperprofilies

        if not client_profile or not landscaper_profile:
            return None

        schedule = Job.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not schedule:
            return None

        return {
            "service_name": schedule.service.name,
            "date": schedule.scheduled_date,
            "time": schedule.scheduled_time,
            "price": float(schedule.service.price or 0),
        }


class SendConnectionRequestSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()

    def validate_receiver_id(self, value):
        request_user = self.context["request"].user

        try:
            receiver = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if receiver == request_user:
            raise serializers.ValidationError("You cannot send request to yourself.")

        if ConnectionRequest.objects.filter(
            Q(sender=request_user, receiver=receiver) |
            Q(sender=receiver, receiver=request_user)
        ).exists():
            raise serializers.ValidationError("Connection already exists.")

        return value

    def create(self, validated_data):
        sender = self.context["request"].user
        receiver = User.objects.get(id=validated_data["receiver_id"])
        return ConnectionRequest.objects.create(sender=sender, receiver=receiver)




class RespondConnectionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "reject"])

    def update(self, instance, validated_data):
        instance.is_accepted = validated_data["action"] == "accept"
        instance.save(update_fields=["is_accepted"])
        return instance


class AcceptedConnectionSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    receiver = UserMiniSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ["id", "sender", "receiver", "created_at"]


class ConnectedUserSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    connected_profile = serializers.DictField()
    created_at = serializers.DateTimeField()
    upcoming_job = serializers.SerializerMethodField()

    def get_upcoming_job(self, obj):
        """
        Get upcoming job between current user and connected user.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        current_user = request.user
        connected_user_id = obj["connected_profile"].get("user_id")
        if not connected_user_id:
            return None

        try:
            connected_user = User.objects.get(id=connected_user_id)
        except User.DoesNotExist:
            return None

        client_profile = None
        landscaper_profile = None

        if hasattr(current_user, "client_profile"):
            client_profile = current_user.client_profile
        elif hasattr(current_user, "landscaperprofilies"):
            landscaper_profile = current_user.landscaperprofilies

        if hasattr(connected_user, "client_profile"):
            client_profile = connected_user.client_profile
        elif hasattr(connected_user, "landscaperprofilies"):
            landscaper_profile = connected_user.landscaperprofilies

        if not client_profile or not landscaper_profile:
            return None

        job = Job.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not job:
            return None

        landscaper_data = None
        if job.landscaper and job.landscaper.user:
            landscaper_user = job.landscaper.user
            landscaper_data = {
                "id": landscaper_user.id,
                "name": getattr(landscaper_user, "name", ""),
                "email": landscaper_user.email,
            }

        return {
            "service_name": job.service.name,
            "date": job.scheduled_date,
            "time": job.scheduled_time,
            "price": float(job.service.price or 0),
            "landscaper": landscaper_data,
        }