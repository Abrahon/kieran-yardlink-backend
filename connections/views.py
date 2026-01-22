from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from .models import ConnectionRequest
from .serializers import ConnectionRequestSerializer


class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        receiver = User.objects.get(id=user_id)

        if receiver == request.user:
            return Response(
                {"detail": "You cannot send request to yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj, created = ConnectionRequest.objects.get_or_create(
            sender=request.user,
            receiver=receiver
        )

        if not created:
            return Response(
                {"detail": "Request already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ConnectionRequestSerializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)




class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        conn = ConnectionRequest.objects.get(
            id=request_id,
            receiver=request.user
        )

        action = request.data.get("action")

        if action == "accept":
            conn.is_accepted = True
        elif action == "reject":
            conn.is_accepted = False
        else:
            return Response(
                {"detail": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conn.save()
        return Response({"status": action}, status=status.HTTP_200_OK)

# incoming request 
class IncomingRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted=None
        )
        serializer = ConnectionRequestSerializer(qs, many=True)
        return Response(serializer.data)

# accept connection friend list
class MyConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            models.Q(sender=request.user) |
            models.Q(receiver=request.user),
            is_accepted=True
        )
        serializer = ConnectionRequestSerializer(qs, many=True)
        return Response(serializer.data)
