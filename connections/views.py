from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .models import ConnectionRequest
from .serializers import (
    ConnectionRequestSerializer,
    SendConnectionRequestSerializer,
    RespondConnectionRequestSerializer,
    # AcceptedConnectionSerializer,
)
# connections/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from accounts.models import User
from .models import ConnectionRequest
from .serializers import ConnectionRequestSerializer

class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Get sent requests (optional)
    def get(self, request):
        requests = ConnectionRequest.objects.filter(
            sender=request.user,
            is_accepted=None
        ).order_by("-created_at")

        serializer = ConnectionRequestSerializer(
            requests, many=True, context={"request": request}
        )
        return Response(serializer.data)

    # Create/send a connection request
    def post(self, request):
        receiver_id = request.data.get("receiver_id")
        if not receiver_id:
            return Response({"error": "receiver_id is required"}, status=400)

        from django.shortcuts import get_object_or_404
        from accounts.models import User

        receiver = get_object_or_404(User, id=receiver_id)

        if receiver == request.user:
            return Response({"error": "You cannot send request to yourself"}, status=400)

        # Avoid duplicate requests
        connection, created = ConnectionRequest.objects.get_or_create(
            sender=request.user,
            receiver=receiver
        )

        from .serializers import ConnectionRequestSerializer
        serializer = ConnectionRequestSerializer(connection, context={"request": request})
        return Response(serializer.data, status=201 if created else 200)


        
class ConnectionInboxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted=None
        ).order_by("-created_at")

        serializer = ConnectionRequestSerializer(
            requests, many=True, context={"request": request}
        )
        return Response(serializer.data)


class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted=None
        ).order_by("-created_at")

        serializer = ConnectionRequestSerializer(requests, many=True)
        return Response(serializer.data)

class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        serializer = ConnectionRequestSerializer(
            requests, many=True, context={"request": request}
        )
        return Response(serializer.data)


# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         try:
#             connection = ConnectionRequest.objects.get(
#                 id=pk,
#                 receiver=request.user,
#                 is_accepted=None
#             )
#         except ConnectionRequest.DoesNotExist:
#             return Response(
#                 {"error": "Request not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = RespondConnectionRequestSerializer(
#             connection,
#             data=request.data
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(
#             ConnectionRequestSerializer(connection).data
#         )
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ConnectionRequest
from .serializers import RespondConnectionRequestSerializer, ConnectionRequestSerializer

class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Only allow pending requests that belong to this user
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            receiver=request.user,
            is_accepted=None
        )

        serializer = RespondConnectionRequestSerializer(
            instance=connection, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return updated connection request with full sender/receiver info
        return Response(
            ConnectionRequestSerializer(connection, context={"request": request}).data
        )


class CancelConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            connection = ConnectionRequest.objects.get(
                id=pk,
                sender=request.user,
                is_accepted=None
            )
        except ConnectionRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        connection.delete()
        return Response(
            {"message": "Request cancelled"},
            status=status.HTTP_204_NO_CONTENT
        )

# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         connections = ConnectionRequest.objects.filter(
#             Q(sender=request.user) | Q(receiver=request.user),
#             is_accepted=True
#         ).order_by("-created_at")

#         serializer = AcceptedConnectionSerializer(
#             connections,
#             many=True,
#             context={"request": request}
#         )
#         return Response(serializer.data)
