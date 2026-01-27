from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import User
from .models import ConnectionRequest
from .serializers import (
    ConnectionRequestDetailSerializer,
    SendConnectionRequestSerializer,
    RespondConnectionRequestSerializer,
    AcceptedConnectionSerializer,
)

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ConnectionRequest

User = get_user_model()

class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        receiver = User.objects.get(
            id=serializer.validated_data["receiver_id"]
        )

        connection = ConnectionRequest.objects.create(
            sender=request.user,
            receiver=receiver
        )

        return Response(
            ConnectionRequestDetailSerializer(
                connection,
                context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )


class ConnectionRequestSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ["id", "receiver_id", "is_accepted", "created_at"]

    def validate_receiver_id(self, value):
        try:
            receiver = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        request_user = self.context["request"].user

        if receiver == request_user:
            raise serializers.ValidationError("You cannot send request to yourself.")

        return receiver

    def create(self, validated_data):
        receiver = validated_data.pop("receiver_id")
        sender = self.context["request"].user

        return ConnectionRequest.objects.create(
            sender=sender,
            receiver=receiver
        )


# inbox/views.py

# class InboxConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Get all pending connection requests for the logged-in user
#         qs = ConnectionRequest.objects.filter(
#             receiver=request.user,
#             is_accepted__isnull=True
#         ).order_by("-created_at")

#         serializer = ConnectionRequestDetailSerializer(qs, many=True, context={"request": request})
#         print("serializer",serializer)
#         return Response(serializer.data)

class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted__isnull=True  # Only pending
        ).order_by("-created_at")

        print("Queryset:", qs)  # Debug: check what it returns
        serializer = ConnectionRequestDetailSerializer(qs, many=True, context={"request": request})
        print("Serialized data:", serializer.data)  # Debug: check serialized output
        return Response(serializer.data)


class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        return Response(ConnectionRequestSerializer(qs, many=True).data)




class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            receiver=request.user,
            is_accepted=None
        )

        serializer = RespondConnectionRequestSerializer(
            instance=connection,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ConnectionRequestSerializer(connection).data)



# class CancelConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, pk):
#         try:
#             connection = ConnectionRequest.objects.get(
#                 id=pk,
#                 sender=request.user,
#                 is_accepted__isnull=True  # fixed here
#             )
#         except ConnectionRequest.DoesNotExist:
#             return Response(
#                 {"error": "Request not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         connection.delete()
#         return Response(
#             {"message": "Request cancelled"},
#             status=status.HTTP_200_OK  # changed from 204
#         )
class CancelConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Fetch the connection where user is either sender or receiver
            connection = ConnectionRequest.objects.get(
                id=pk,
                is_accepted__isnull=True,
            )
            if request.user != connection.sender:
                # Only the sender can cancel pending requests
                return Response(
                    {"error": "Only sender can cancel this request"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ConnectionRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        connection.delete()
        return Response(
            {"message": "Request cancelled"},
            status=status.HTTP_200_OK
        )


# connections/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from connections.models import ConnectionRequest
from profiles.models import LandscaperProfilies, ClientProfile
from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
from profiles.serializers import ConnectedUserSerializer
class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]



class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all accepted connections where the current user is sender or receiver
        connections = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            is_accepted=True
        ).order_by("-created_at")

        response_data = []

        for conn in connections:
            # Determine the connected user (not the current user)
            connected_user = conn.receiver if conn.sender == request.user else conn.sender

            # Try to get landscaper profile
            try:
                profile = LandscaperProfilies.objects.get(user=connected_user)
                profile_data = LandscaperProfileSerializer(profile).data
                profile_data["type"] = "landscaper"
            except LandscaperProfilies.DoesNotExist:
                # Try to get client profile
                try:
                    profile = ClientProfile.objects.get(user=connected_user)
                    profile_data = ClientProfileSerializer(profile).data
                    profile_data["type"] = "client"
                except ClientProfile.DoesNotExist:
                    # If no profile, return basic info
                    profile_data = {
                        "user_id": connected_user.id,
                        "email": connected_user.email,
                        "name": getattr(connected_user, "name", ""),
                        "type": "unknown"
                    }

            response_data.append({
                "connection_id": conn.id,
                "connected_profile": profile_data,
                "created_at": conn.created_at
            })

        # Serialize using ConnectedUserSerializer (optional but keeps structure consistent)
        serializer = ConnectedUserSerializer(response_data, many=True)
        return Response(serializer.data)


class RemoveConnectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            is_accepted=True
        )

        if request.user not in [connection.sender, connection.receiver]:
            return Response(
                {"detail": "Permission denied"},
                status=403
            )

        connection.delete()
        return Response(
            {"message": "Connection removed"}
        )
