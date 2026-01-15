# invitations/views.py
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from accounts.models import User
from profiles.models import WorkerProfile
from .models import TeamInvitation
from .serializers import SendInvitationSerializer, AcceptInvitationSerializer
from .permissions import IsProLandscaper


# =========================
# SEND INVITATION
# =========================
class SendInvitationView(CreateAPIView):
    serializer_class = SendInvitationSerializer
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def perform_create(self, serializer):
        user = self.request.user
        landscaper = user.landscaper_profile
        email = serializer.validated_data["email"]

        invitation = TeamInvitation.objects.create(
            inviter=user,
            landscaper=landscaper,
            email=email
        )

        invite_link = f"http://localhost:8000/accept-invite/{invitation.token}"

        send_mail(
            subject="You're invited to join a landscaper team",
            message=f"Accept invitation using this link: {invite_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )


# =========================
# ACCEPT INVITATION
# =========================
class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        invitation = TeamInvitation.objects.filter(
            token=token,
            status="pending"
        ).first()

        if not invitation or invitation.is_expired():
            return Response(
                {"detail": "Invitation invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, created = User.objects.get_or_create(
            email=invitation.email,
            defaults={
                "name": serializer.validated_data["name"],
                "role": "worker"
            }
        )

        user.set_password(serializer.validated_data["password"])
        user.save()

        WorkerProfile.objects.update_or_create(
            user=user,
            defaults={
                "name": serializer.validated_data["name"],
                "pro_landscaper": invitation.landscaper,
            }
        )

        invitation.status = "accepted"
        invitation.accepted_at = timezone.now()
        invitation.save()

        return Response(
            {"detail": "Invitation accepted successfully"},
            status=status.HTTP_200_OK
        )


# =========================
# PENDING INVITATIONS
# =========================
class InvitationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = (
            "id",
            "email",
            "status",
            "expires_at",
            "created_at",
            "token",
        )


class PendingInvitationListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]
    serializer_class = InvitationListSerializer

    def get_queryset(self):
        return TeamInvitation.objects.filter(
            landscaper=self.request.user.landscaper_profile,
            status="pending"
        )


# =========================
# CANCEL INVITATION
# =========================
class CancelInvitationView(APIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def delete(self, request, invitation_id):
        invitation = TeamInvitation.objects.filter(
            id=invitation_id,
            landscaper=request.user.landscaper_profile,
            status="pending"
        ).first()

        if not invitation:
            return Response(
                {"detail": "Pending invitation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        invitation.delete()
        return Response({"detail": "Invitation cancelled"})


# =========================
# DELETE INVITATION
# =========================
class DeleteInvitationView(APIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def delete(self, request, invitation_id):
        invitation = TeamInvitation.objects.filter(
            id=invitation_id,
            landscaper=request.user.landscaper_profile
        ).first()

        if not invitation:
            return Response(
                {"detail": "Invitation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        invitation.delete()
        return Response({"detail": "Invitation deleted"})


# =========================
# BLOCK WORKER
# =========================
class BlockWorkerView(APIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def post(self, request, worker_id):
        # ✅ Use the correct field 'pro_landscaper'
        worker = WorkerProfile.objects.filter(
            id=worker_id,
            pro_landscaper=request.user.landscaper_profile
        ).select_related("user").first()

        if not worker:
            return Response(
                {"detail": "Worker not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Block worker
        worker.is_blocked = True
        worker.user.is_active = False
        worker.user.save()
        worker.save()

        return Response(
            {"detail": "Worker blocked successfully"},
            status=status.HTTP_200_OK
        )
