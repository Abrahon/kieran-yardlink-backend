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
class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        receiver_id = serializer.validated_data["receiver_id"]

        connection = ConnectionRequest.objects.create(
            sender=request.user,
            receiver_id=receiver_id
        )

        return Response(
            ConnectionRequestSerializer(connection).data,
            status=status.HTTP_201_CREATED
        )
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
            sender=request.user,
            is_accepted=None
        ).order_by("-created_at")

        serializer = ConnectionRequestSerializer(requests, many=True)
        return Response(serializer.data)

class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            connection = ConnectionRequest.objects.get(
                id=pk,
                receiver=request.user,
                is_accepted=None
            )
        except ConnectionRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RespondConnectionRequestSerializer(
            connection,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ConnectionRequestSerializer(connection).data
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
