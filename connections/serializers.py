# # connections/serializers.py
# # connections/serializers.py
# from rest_framework import serializers
# from .models import ConnectionRequest
# from profiles.serializers import ClientProfileSerializer
# from landscapers.serializers import LandscaperProfileSerializer
# from accounts.models import User
# from connections.serializers import ConnectedUserSerializer


# # class ConnectionRequestSerializer(serializers.ModelSerializer):
# #     sender_profile = serializers.SerializerMethodField()
# #     receiver_profile = serializers.SerializerMethodField()

# #     class Meta:
# #         model = ConnectionRequest
# #         fields = [
# #             "id",
# #             "is_accepted",
# #             "created_at",
# #             "sender_profile",
# #             "receiver_profile",
# #         ]

# #     def get_sender_profile(self, obj):
# #         user = obj.sender
# #         if hasattr(user, "clientprofile"):
# #             return ClientProfileSerializer(user.clientprofile).data
# #         if hasattr(user, "landscaperprofilies"):
# #             return LandscaperProfileSerializer(user.landscaperprofilies).data
# #         return None

# #     def get_receiver_profile(self, obj):
# #         user = obj.receiver
# #         if hasattr(user, "clientprofile"):
# #             return ClientProfileSerializer(user.clientprofile).data
# #         if hasattr(user, "landscaperprofilies"):
# #             return LandscaperProfileSerializer(user.landscaperprofilies).data
# #         return None
# from rest_framework import serializers
# from .models import ConnectionRequest
# from profiles.serializers import ClientProfileSerializer
# from landscapers.serializers import LandscaperProfileSerializer


# class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
#     sender_profile = serializers.SerializerMethodField()
#     receiver_profile = serializers.SerializerMethodField()

#     class Meta:
#         model = ConnectionRequest
#         fields = [
#             "id",
#             "is_accepted",
#             "created_at",
#             "sender_profile",
#             "receiver_profile",
#         ]

#     def _build_profile(self, user):
#         # CLIENT
#         if hasattr(user, "clientprofile"):
#             data = ClientProfileSerializer(
#                 user.clientprofile,
#                 context=self.context
#             ).data
#             data["type"] = "client"
#             return data

#         # LANDSCAPER
#         if hasattr(user, "landscaperprofilies"):
#             data = LandscaperProfileSerializer(
#                 user.landscaperprofilies,
#                 context=self.context
#             ).data
#             data["type"] = "landscaper"
#             return data

#         return None

#     def get_sender_profile(self, obj):
#         return self._build_profile(obj.sender)

#     def get_receiver_profile(self, obj):
#         return self._build_profile(obj.receiver)

        
# class SendConnectionRequestSerializer(serializers.Serializer):
#     receiver_id = serializers.IntegerField()

#     def validate_receiver_id(self, value):
#         request_user = self.context["request"].user

#         try:
#             receiver = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User not found.")

#         if receiver == request_user:
#             raise serializers.ValidationError("You cannot send request to yourself.")

#         # Prevent duplicates (both directions)
#         if ConnectionRequest.objects.filter(
#             sender=request_user,
#             receiver=receiver
#         ).exists() or ConnectionRequest.objects.filter(
#             sender=receiver,
#             receiver=request_user
#         ).exists():
#             raise serializers.ValidationError("Connection already exists.")

#         return value

        

# class RespondConnectionRequestSerializer(serializers.Serializer):
#     action = serializers.ChoiceField(choices=["accept", "reject"])

#     def update(self, instance, validated_data):
#         instance.is_accepted = validated_data["action"] == "accept"
#         instance.save(update_fields=["is_accepted"])
#         return instance


# class UserMiniSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "name", "email", "role"]


# class AcceptedConnectionSerializer(serializers.ModelSerializer):
#     sender = UserMiniSerializer(read_only=True)
#     receiver = UserMiniSerializer(read_only=True)

#     class Meta:
#         model = ConnectionRequest
#         fields = ["id", "sender", "receiver", "created_at"]

# connections/serializers.py
from rest_framework import serializers
from .models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer
from landscapers.serializers import BusinessLandscaperProfileSerializer
from accounts.models import User


class UserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user info for quick references.
    """
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]




# class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
#     sender_profile = serializers.SerializerMethodField()
#     receiver_profile = serializers.SerializerMethodField()
#     is_accepted = serializers.SerializerMethodField()  # override to convert null → false

#     class Meta:
#         model = ConnectionRequest
#         fields = ['id', 'is_accepted', 'created_at', 'sender_profile', 'receiver_profile']

#     def get_is_accepted(self, obj):
#         """
#         Convert None (pending) → False for API responses
#         """
#         return bool(obj.is_accepted)

#     def _get_profile(self, user):
#         """
#         Return only necessary profile info depending on user type.
#         """
#         # Check if user is a landscaper
#         try:
#             profile = LandscaperProfilies.objects.get(user=user)
#             data = LandscaperProfileSerializer(profile).data
#             data["type"] = "landscaper"
#             return data
#         except LandscaperProfilies.DoesNotExist:
#             pass

#         # Check if user is a client
#         try:
#             profile = ClientProfile.objects.get(user=user)
#             data = ClientProfileSerializer(profile).data
#             data["type"] = "client"
#             return data
#         except ClientProfile.DoesNotExist:
#             pass

#         # Fallback minimal info
#         return {"user_id": user.id, "email": user.email, "type": "unknown"}

#     def get_sender_profile(self, obj):
#         return self._get_profile(obj.sender)

#     def get_receiver_profile(self, obj):
#         return self._get_profile(obj.receiver)

# from rest_framework import serializers
# from profiles.models import LandscaperProfilies, ClientProfile
# from connections.models import ConnectionRequest
# from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer


# class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
#     sender_profile = serializers.SerializerMethodField()
#     receiver_profile = serializers.SerializerMethodField()
#     is_accepted = serializers.SerializerMethodField()  # override to convert null → false

#     class Meta:
#         model = ConnectionRequest
#         fields = ['id', 'is_accepted', 'created_at', 'sender_profile', 'receiver_profile']

#     def get_is_accepted(self, obj):
#         """
#         Convert None (pending) → False for API responses
#         """
#         return bool(obj.is_accepted)

#     def _get_profile(self, user):
#         """
#         Return only necessary profile info depending on user type.
#         """
#         # Check if user is a landscaper
#         try:
#             profile = LandscaperProfilies.objects.get(user=user)
#             data = LandscaperProfileSerializer(profile).data
#             data["type"] = "landscaper"
#             return data
#         except LandscaperProfilies.DoesNotExist:
#             pass

#         # Check if user is a client
#         try:
#             profile = ClientProfile.objects.get(user=user)
#             data = ClientProfileSerializer(profile).data
#             data["type"] = "client"
#             return data
#         except ClientProfile.DoesNotExist:
#             pass

#         # Fallback minimal info
#         return {"user_id": user.id, "email": user.email, "type": "unknown"}

#     def get_sender_profile(self, obj):
#         return self._get_profile(obj.sender)

#     def get_receiver_profile(self, obj):
#         return self._get_profile(obj.receiver)
from rest_framework import serializers
from profiles.models import LandscaperProfilies, ClientProfile
from connections.models import ConnectionRequest
from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
from django.db.models import Q

class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()
    is_accepted = serializers.SerializerMethodField()  # override to convert null → false
    already_sent = serializers.SerializerMethodField()  # NEW FIELD

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'is_accepted', 'created_at', 'sender_profile', 'receiver_profile', 'already_sent']

    def get_is_accepted(self, obj):
        """
        Convert None (pending) → False for API responses
        """
        return bool(obj.is_accepted)

    def _get_profile(self, user):
        """
        Return only necessary profile info depending on user type.
        """
        # Check if user is a landscaper
        try:
            profile = LandscaperProfilies.objects.get(user=user)
            data = LandscaperProfileSerializer(profile).data
            data["type"] = "landscaper"
            return data
        except LandscaperProfilies.DoesNotExist:
            pass

        # Check if user is a client
        try:
            profile = ClientProfile.objects.get(user=user)
            data = ClientProfileSerializer(profile).data
            data["type"] = "client"
            return data
        except ClientProfile.DoesNotExist:
            pass

        # Fallback minimal info
        return {"user_id": user.id, "email": user.email, "type": "unknown"}

    def get_sender_profile(self, obj):
        return self._get_profile(obj.sender)

    def get_receiver_profile(self, obj):
        return self._get_profile(obj.receiver)

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

class SendConnectionRequestSerializer(serializers.Serializer):
    """
    Serializer to send a new connection request.
    """
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
