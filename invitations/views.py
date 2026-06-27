# invitations/views.py
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from .models import TeamInvitation
from accounts.models import User
from profiles.models import WorkerProfile
from .models import TeamInvitation
from .serializers import SendInvitationSerializer,AcceptInvitationSerializer,InvitationListSerializer
from .permissions import IsProLandscaper
from invitations.models import TeamInvitation
from django.core.exceptions import ValidationError

from subscriptions.helpers import can_add_team_member

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from django.core.mail import EmailMultiAlternatives
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


# =========================
# SEND INVITATION
# =========================




class SendInvitationView(CreateAPIView):
    serializer_class = SendInvitationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        user = request.user
        landscaper = user.landscaper_profile
        email = request.data.get("email")

        # -------------------------
        # LIMIT CHECK
        # -------------------------
        if not can_add_team_member(user):
            return Response(
                {
                    "success": False,
                    "message": "Team member limit reached for your plan"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = TeamInvitation.objects.create(
            inviter=user,
            landscaper=landscaper,
            email=email
        )

        # Full URL
        invite_link = (

            f"http://localhost:5400/accept-invite?token={invitation.token}"
        )
            

        # HTML Email
        html_content = f"""
        <h2>Team Invitation</h2>

        <p>You have been invited to join a landscaper team.</p>

        <p>
            <a href="{invite_link}"
               style="
                    background:#28a745;
                    color:white;
                    padding:10px 20px;
                    text-decoration:none;
                    border-radius:5px;
                    display:inline-block;
               ">
                Accept Invitation
            </a>
        </p>

        <p>If the button does not work, use this URL:</p>

        <p>{invite_link}</p>
        """

        email_message = EmailMultiAlternatives(
            subject="You're invited to join a landscaper team",
            body=f"Accept invitation: {invite_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        email_message.attach_alternative(
            html_content,
            "text/html"
        )

        email_message.send()

        return Response(
            {
                "success": True,
                "message": "Invitation sent successfully",
                "invite_link": invite_link
            },
            status=status.HTTP_201_CREATED
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



def invitation_success(request):
    return render(
        request,
        "http://localhost:5400/accept-invite/success"
    )





# =========================
# PENDING INVITATIONS
# =========================


class PendingInvitationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
from invitations.models import TeamInvitation, InvitationStatus
from accounts.models import User
from profiles.models import WorkerProfile 

class WorkerBlockToggleView(APIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]

    def post(self, request, worker_id):

        action = request.data.get("action")
        if action not in ["block", "unblock"]:
            return Response(
                {"detail": "Invalid action. Use 'block' or 'unblock'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔥 FIX 1: DO NOT restrict only ACCEPTED
        invitation = TeamInvitation.objects.filter(
            id=worker_id,
            landscaper=request.user.landscaper_profile
        ).first()

        if not invitation:
            return Response(
                {"detail": "Invitation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        worker_user = User.objects.filter(email=invitation.email).first()

        if not worker_user:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        worker = WorkerProfile.objects.filter(
            user=worker_user,
            pro_landscaper=request.user.landscaper_profile
        ).first()

        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # -------------------------
        # BLOCK / UNBLOCK
        # -------------------------
        if action == "block":
            worker.is_blocked = True
            worker.user.is_active = False
            invitation.status = InvitationStatus.BLOCKED
            message = "Worker blocked successfully"

        else:
            worker.is_blocked = False
            worker.user.is_active = True
            invitation.status = InvitationStatus.ACCEPTED
            message = "Worker unblocked successfully"

        # 🔥 SAVE EVERYTHING (VERY IMPORTANT FIX)
        worker.user.save(update_fields=["is_active"])
        worker.save(update_fields=["is_blocked"])
        invitation.save(update_fields=["status"])

        return Response(
            {"detail": message},
            status=status.HTTP_200_OK
        )

class AcceptedInvitationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvitationListSerializer

    def get_queryset(self):
        return TeamInvitation.objects.filter(
            landscaper=self.request.user.landscaper_profile,
            status=InvitationStatus.ACCEPTED,
        ).exclude(
            email__in=WorkerProfile.objects.filter(is_blocked=True).values("user__email")
        )

def accept_invite_page(request, token):
    invitation = get_object_or_404(
        TeamInvitation,
        token=token,
        status="pending"
    )
    return render(request, "invitations/accept_invite.html", {"token": token})




class BlockedWorkerListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvitationListSerializer

    def get_queryset(self):
        return TeamInvitation.objects.filter(
            landscaper=self.request.user.landscaper_profile,
            status=InvitationStatus.BLOCKED
        )

