

# connections/serializers.py
from rest_framework import serializers
from .models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer
from landscapers.serializers import BusinessLandscaperProfileSerializer
from accounts.models import User
from rest_framework import serializers
from services.models import ServiceSchedule
from profiles.models import LandscaperProfilies
from rest_framework import serializers
from profiles.models import LandscaperProfilies, ClientProfile
from connections.models import ConnectionRequest
from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
from django.db.models import Q
from datetime import timedelta
from django.utils.timezone import now



class UserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user info for quick references.
    """
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]

# class ConnectionRequestSerializer(serializers.ModelSerializer):
#     receiver_id = serializers.IntegerField(write_only=True)

#     class Meta:
#         model = ConnectionRequest
#         fields = ["id", "receiver_id", "is_accepted", "created_at"]

#     def validate_receiver_id(self, value):
#         try:
#             receiver = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User not found.")

#         request_user = self.context["request"].user

#         if receiver == request_user:
#             raise serializers.ValidationError("You cannot send request to yourself.")

#         return receiver

#     def create(self, validated_data):
#         receiver = validated_data.pop("receiver_id")
#         sender = self.context["request"].user

#         return ConnectionRequest.objects.create(
#             sender=sender,
#             receiver=receiver
#         )


class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()
    already_sent = serializers.SerializerMethodField()  
    scheduled_job = serializers.SerializerMethodField()
    sent_since = serializers.SerializerMethodField()  # <-- Add here
    
    class Meta:
        model = ConnectionRequest
        fields = ['id', 'is_accepted', 'created_at', 'sender_profile', 'receiver_profile', 'already_sent', 'sent_since', 'scheduled_job']


    def get_is_accepted(self, obj):
        """
        Convert None (pending) → False for API responses
        """
        return bool(obj.is_accepted)

    # def _get_profile(self, user):
    #     """
    #     Return only necessary profile info depending on user type.
    #     """
    #     # Check if user is a landscaper
    #     try:
    #         profile = LandscaperProfilies.objects.get(user=user)
    #         data = LandscaperProfileSerializer(profile).data
    #         data["type"] = "landscaper"
    #         return data
    #     except LandscaperProfilies.DoesNotExist:
    #         pass

    #     # Check if user is a client
    #     try:
    #         profile = ClientProfile.objects.get(user=user)
    #         data = ClientProfileSerializer(profile).data
    #         data["type"] = "client"
    #         return data
    #     except ClientProfile.DoesNotExist:
    #         pass

    #     # Fallback minimal info
    #     return {"user_id": user.id, "email": user.email, "type": "unknown"}

    def _get_profile(self, user):
        """
        Return the user's profile depending on role/type:
        - If landscaper, prefer BusinessProfile
        - Fallback to LandscaperProfilies (basic info)
        - If client, use ClientProfile
        """
        # Try to get BusinessProfile first
        business_profile = getattr(user, "landscaper_profile", None)  # related_name from BusinessProfile
        if business_profile:
            return {
                **LandscaperProfileSerializer(business_profile, context=self.context).data,
                "type": "landscaper"
            }

        # Fallback to basic profile
        basic_profile = getattr(user, "landscaperprofilies", None)
        
        if basic_profile:
            return {
                "user_id": user.id,
                "name": basic_profile.name,
                "phone": basic_profile.phone,
                "image": basic_profile.image.url if basic_profile.image else None,
                "type": "landscaper_basic"
            }

        # Client profile
        client_profile = getattr(user, "client_profile", None)
        if client_profile:
            return {
                **ClientProfileSerializer(client_profile, context=self.context).data,
                "type": "client"
            }

        # Minimal fallback
        return {"user_id": user.id, "email": user.email, "type": "unknown"}


    def get_sent_since(self, obj):


        """
        Calculates how long ago the request was sent
        """
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
        else:
            return obj.created_at.strftime("%Y-%m-%d")

    def get_sender_profile(self, obj):
        return self._get_profile(obj.sender)

    def get_receiver_profile(self, obj):
        return self._get_profile(obj.receiver)
    
    def get_scheduled_job(self, obj):
        if obj.is_accepted is None or obj.is_accepted is False:
            return None

        # Determine landscaper and client
        try:
            if hasattr(obj.sender, "clientprofile"):
                client = obj.sender.clientprofile
                landscaper = obj.receiver.landscaperprofilies
            else:
                client = obj.receiver.clientprofile
                landscaper = obj.sender.landscaperprofilies
        except (ClientProfile.DoesNotExist, LandscaperProfilies.DoesNotExist):
            return None

        # Fetch pending (upcoming) job
        schedule = ServiceSchedule.objects.filter(
            landscaper=landscaper,
            client=client,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not schedule:
            return None

        return {
            "service_name": schedule.service.name,
            "date": schedule.scheduled_date,
            "time": schedule.scheduled_time,
            "price": float(schedule.service.price or 0)
        }



    def get_already_sent(self, obj):
        """
        Returns True if a request already exists between sender and receiver.
        Includes all statuses: pending, accepted, rejected.
        """
        exists = ConnectionRequest.objects.filter(
            Q(sender=obj.sender, receiver=obj.receiver) |
            Q(sender=obj.receiver, receiver=obj.sender)
        ).exists()
        return exists



# class SendConnectionRequestSerializer(serializers.Serializer):
#     """
#     Serializer to send a new connection request.
#     """
#     receiver_id = serializers.IntegerField()

#     def validate_receiver_id(self, value):
#         request_user = self.context["request"].user

#         try:
#             receiver = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User not found.")

#         if receiver == request_user:
#             raise serializers.ValidationError("You cannot send request to yourself.")

#         # Prevent duplicates in both directions
#         if ConnectionRequest.objects.filter(sender=request_user, receiver=receiver).exists() or \
#            ConnectionRequest.objects.filter(sender=receiver, receiver=request_user).exists():
#             raise serializers.ValidationError("Connection already exists.")

#         return value
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

        # Prevent duplicates in both directions
        if ConnectionRequest.objects.filter(sender=request_user, receiver=receiver).exists() or \
           ConnectionRequest.objects.filter(sender=receiver, receiver=request_user).exists():
            raise serializers.ValidationError("Connection already exists.")

        return value


class RespondConnectionRequestSerializer(serializers.Serializer):
    """
    Accept or reject a connection request.
    """
    action = serializers.ChoiceField(choices=["accept", "reject"])

    def update(self, instance, validated_data):
        instance.is_accepted = validated_data["action"] == "accept"
        instance.save(update_fields=["is_accepted"])
        return instance


class AcceptedConnectionSerializer(serializers.ModelSerializer):
    """
    Minimal accepted connection info for list views (friend list).
    """
    sender = UserMiniSerializer(read_only=True)
    receiver = UserMiniSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ["id", "sender", "receiver", "created_at"]


class ConnectedUserSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    connected_profile = serializers.DictField()
    created_at = serializers.DateTimeField()
    upcoming_job = serializers.SerializerMethodField()  # <-- add this

    def get_upcoming_job(self, obj):
        try:
            client_profile = getattr(obj['connected_profile']['user'], 'clientprofile', None)
            landscaper_profile = getattr(obj['connected_profile']['user'], 'landscaper_profile', None)
            if not client_profile or not landscaper_profile:
                return None

            job = ServiceSchedule.objects.filter(
                client=client_profile,
                landscaper=landscaper_profile,
                is_completed=False
            ).order_by("scheduled_date", "scheduled_time").first()

            if not job:
                return None

            return {
                "service_name": job.service.name,
                "date": job.scheduled_date,
                "time": job.scheduled_time,
                "price": job.service.price
            }
        except:
            return None

            


class ConnectedUserSerializer(serializers.Serializer):
    connection_id = serializers.IntegerField()
    connected_profile = serializers.DictField()  # client profile dict
    created_at = serializers.DateTimeField()
    upcoming_job = serializers.SerializerMethodField()

    def get_upcoming_job(self, obj):
        """
        Fetch the upcoming job for this connection.
        Use the client info from connected_profile and fetch landscaper from job.
        """
        try:
            # Get the client user ID from the connected profile
            client_user_id = obj['connected_profile'].get('user_id')
            if not client_user_id:
                return None

            # Get client profile object
            from profiles.models import ClientProfile
            client_profile = ClientProfile.objects.filter(user_id=client_user_id).first()
            if not client_profile:
                return None

            # Get the first upcoming scheduled job for this client
            job = ServiceSchedule.objects.filter(
                client=client_profile,
                is_completed=False
            ).order_by("scheduled_date", "scheduled_time").first()

            if not job:
                return None

            # Prepare landscaper data if available
            landscaper_data = None
            if job.landscaper:
                landscaper_user = job.landscaper.user
                landscaper_data = {
                    "id": landscaper_user.id,
                    "name": getattr(landscaper_user, "name", ""),
                    "email": landscaper_user.email,
                    "phone": getattr(landscaper_user, "phone", ""),
                }

            return {
                "service_name": job.service.category or job.service.name,
                "date": job.scheduled_date,
                "time": job.scheduled_time,
                "price": float(job.service.price or 0),
                "landscaper": landscaper_data
            }

        except Exception as e:
            # Optionally log e here
            return None
