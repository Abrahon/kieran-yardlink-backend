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

        invite_link = f"https://zznkjkkp-8000.inc1.devtunnels.ms/{invitation.token}"

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

        # 🔥 STEP 1: get invitation by ID
        invitation = TeamInvitation.objects.filter(
            id=worker_id,
            status=InvitationStatus.ACCEPTED
        ).first()

        if not invitation:
            return Response(
                {"detail": "Accepted invitation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔥 STEP 2: get user by email (IMPORTANT FIX)
        worker_user = User.objects.filter(email=invitation.email).first()

        if not worker_user:
            return Response(
                {"detail": "User not found for this invitation"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔥 STEP 3: get worker profile
        worker = WorkerProfile.objects.filter(
            user=worker_user,
            pro_landscaper=request.user.landscaper_profile
        ).select_related("user").first()

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
            message = "Worker blocked successfully"
        else:
            worker.is_blocked = False
            worker.user.is_active = True
            message = "Worker unblocked successfully"

        worker.user.save(update_fields=["is_active"])
        worker.save(update_fields=["is_blocked"])

        return Response(
            {"detail": message},
            status=status.HTTP_200_OK
        )

class AcceptedInvitationListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsProLandscaper]
    serializer_class = InvitationListSerializer

    def get_queryset(self):
        return TeamInvitation.objects.filter(
            landscaper=self.request.user.landscaper_profile,
            status="accepted"
        )

# # invitations/views.py
# class AcceptedWorkerListView(ListAPIView):
#     permission_classes = [IsAuthenticated, IsProLandscaper]
#     serializer_class = WorkerProfileSerializer

#     def get_queryset(self):
#         return WorkerProfile.objects.filter(
#             pro_landscaper=self.request.user.landscaper_profile
#         ).select_related("user")
# invitations/views.py


def accept_invite_page(request, token):
    invitation = get_object_or_404(
        TeamInvitation,
        token=token,
        status="pending"
    )
    return render(request, "invitations/accept_invite.html", {"token": token})



# invitations/views.py

# from landscapers.models import BusinessEmployee, EmployeePermission

# # =========================
# # ACCEPT INVITATION
# # =========================
# class AcceptInvitationView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request, token):
#         invitation = TeamInvitation.objects.filter(
#             token=token,
#             status="pending"
#         ).select_related("landscaper").first()

#         if not invitation or invitation.is_expired():
#             return Response(
#                 {"detail": "Invitation invalid or expired"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         serializer = AcceptInvitationSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         # 1️⃣ Create or get user
#         user, created = User.objects.get_or_create(
#             email=invitation.email,
#             defaults={
#                 "name": serializer.validated_data["name"],
#                 "role": "worker",
#                 "is_active": True
#             }
#         )

#         user.set_password(serializer.validated_data["password"])
#         user.save()

#         # 2️⃣ Create / Update Worker Profile
#         WorkerProfile.objects.update_or_create(
#             user=user,
#             defaults={
#                 "name": serializer.validated_data["name"],
#                 "pro_landscaper": invitation.landscaper,
#             }
#         )

#         # 3️⃣ Create BusinessEmployee
#         employee, emp_created = BusinessEmployee.objects.get_or_create(
#             landscaper=invitation.landscaper,
#             user=user,
#             defaults={
#                 "is_active": True
#             }
#         )

#         # 4️⃣ Create Default Permissions (only if employee newly created)
#         if emp_created:
#             EmployeePermission.objects.create(
#                 employee=employee,
#                 can_access_calendar=True,
#                 can_manage_services=False,
#                 can_manage_business_profile=False,
#                 can_access_messages=True
#             )

#         # 5️⃣ Mark invitation accepted
#         invitation.status = "accepted"
#         invitation.accepted_at = timezone.now()
#         invitation.save()

#         return Response(
#             {"detail": "Invitation accepted successfully"},
#             status=status.HTTP_200_OK
        # )