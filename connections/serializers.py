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
from landscapers.serializers import LandscaperProfileSerializer
from accounts.models import User


class UserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user info for quick references.
    """
    class Meta:
        model = User
        fields = ["id", "name", "email", "role"]


class ConnectionRequestDetailSerializer(serializers.ModelSerializer):
    """
    Full detail for connection requests with full sender and receiver profile.
    """
    sender_profile = serializers.SerializerMethodField()
    receiver_profile = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = [
            "id",
            "is_accepted",
            "created_at",
            "sender_profile",
            "receiver_profile",
        ]

    def _build_profile(self, user):
        """
        Return full profile data depending on user type (client or landscaper).
        Adds a "type" key to distinguish.
        """
        if hasattr(user, "clientprofile"):
            data = ClientProfileSerializer(user.clientprofile, context=self.context).data
            data["type"] = "client"
            return data

        if hasattr(user, "landscaperprofilies"):
            data = LandscaperProfileSerializer(user.landscaperprofilies, context=self.context).data
            data["type"] = "landscaper"
            return data

        # fallback minimal info
        return UserMiniSerializer(user, context=self.context).data

    def get_sender_profile(self, obj):
        return self._build_profile(obj.sender)

    def get_receiver_profile(self, obj):
        return self._build_profile(obj.receiver)


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
