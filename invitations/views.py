# invitations/views.py
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from profiles.models import WorkerProfile 
from .models import TeamInvitation
from .serializers import SendInvitationSerializer
from .permissions import IsProLandscaper
from rest_framework.views import APIView
from django.utils import timezone
from accounts.models import User
from .serializers import AcceptInvitationSerializer
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from .models import TeamInvitation
from .serializers import SendInvitationSerializer
from .permissions import IsProLandscaper


class SendInvitationView(CreateAPIView):
    serializer_class = SendInvitationSerializer
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def perform_create(self, serializer):
        # Everything below must be indented
        user = self.request.user
        landscaper = user.landscaper_profile
        email = serializer.validated_data["email"]

        invitation = TeamInvitation.objects.create(
            inviter=user,
            landscaper=landscaper,
            email=email
        )

        # Temporary link for now (since no frontend yet)
        invite_link = f"http://localhost:8000/accept-invite/{invitation.token}"

        send_mail(
            subject="You're invited to join a landscaper team",
            message=f"Accept invitation using this link: {invite_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )



# class AcceptInvitationView(APIView):
#     authentication_classes = []
#     permission_classes = []

#     def post(self, request, token):
#         invitation = TeamInvitation.objects.filter(
#             token=token,
#             status="pending"
#         ).first()

#         if not invitation or invitation.is_expired():
#             return Response(
#                 {"detail": "Invitation invalid or expired"},
#                 status=400
#             )

#         serializer = AcceptInvitationSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user, created = User.objects.get_or_create(
#             email=invitation.email,
#             defaults={
#                 "name": serializer.validated_data["name"],
#                 "role": "client",
#             }
#         )

#         if created:
#             user.set_password(serializer.validated_data["password"])
#             user.save()

#         invitation.status = "accepted"
#         invitation.accepted_at = timezone.now()
#         invitation.save()

#         return Response({"detail": "Invitation accepted"})
# invitations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from accounts.models import User
from profiles.models import WorkerProfile  # ✅ Import WorkerProfile
from .models import TeamInvitation
from rest_framework.permissions import AllowAny

# Serializer for accepting invitation
class AcceptInvitationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

class AcceptInvitationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]  # Anyone with token can accept

    def post(self, request, token):
        # Get the invitation
        invitation = TeamInvitation.objects.filter(
            token=token,
            status="pending"
        ).first()

        if not invitation or invitation.is_expired():
            return Response(
                {"detail": "Invitation invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate input
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1️⃣ Get or CREATE worker User
        try:
            user = User.objects.get(email=invitation.email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=invitation.email,
                name=serializer.validated_data["name"],
                role="worker",
                password=serializer.validated_data["password"]
            )
        else:
            # User exists (update their info)
            user.name = serializer.validated_data["name"]
            user.role = "worker"
            user.set_password(serializer.validated_data["password"])
            user.save()

        # 2️⃣ Create or update WorkerProfile
        WorkerProfile.objects.update_or_create(
            user=user,
            defaults={
                "name": serializer.validated_data["name"],
                "pro_landscaper": invitation,  # link correct TeamInvitation
            }
        )

        # 3️⃣ Mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = timezone.now()
        invitation.save()

        return Response(
            {"detail": "Invitation accepted successfully. You can now log in."},
            status=status.HTTP_200_OK
        )
