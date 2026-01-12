from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import AdminProfile
from .models import WorkerProfile
from .models import ClientProfile
from .serializers import AdminProfileSerializer,ChangePasswordSerializer,WorkerProfileSerializer,ClientProfileSerializer
from rest_framework import generics, permissions
from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from accounts.models import RoleChoices 
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q
from common.permissions import IsClient,IsAdmin,IsLandscaper,IsWorker
# from services.permissions import IsLandscaper
from invitations.models import TeamInvitation, InvitationStatus


# admin profile
class AdminProfileView(RetrieveUpdateAPIView):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        # Get the AdminProfile for the logged-in user, create if missing
        profile, _ = AdminProfile.objects.get_or_create(user=self.request.user)
        return profile


# worker profile
class WorkerProfileView(generics.GenericAPIView):
    """
    Get profile for a worker or landscaper:
    - Worker: own profile
    - Landscaper: all accepted workers + self profile
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAuthenticated, IsWorker]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        user = request.user

        if user.role == "worker":
            # Worker sees own profile
            profile = get_object_or_404(WorkerProfile, user=user)
            return Response(self.get_serializer(profile).data)

        if user.role == "landscaper":
            worker_id = request.query_params.get("worker_id")

            # Get all accepted invitations for this landscaper
            accepted_invitations = TeamInvitation.objects.filter(
                landscaper=user.landscaper_profile,
                status=InvitationStatus.ACCEPTED
            )

            if worker_id:
                # Get specific worker profile
                profile = get_object_or_404(
                    WorkerProfile,
                    id=worker_id,
                    pro_landscaper__in=accepted_invitations
                )
                return Response(self.get_serializer(profile).data)

            # Get all worker profiles linked to accepted invitations
            profiles = WorkerProfile.objects.filter(
                Q(pro_landscaper__in=accepted_invitations) | Q(user=user)
            )
            return Response(self.get_serializer(profiles, many=True).data)

        raise PermissionDenied("Access denied")


# class WorkerProfileView(generics.GenericAPIView):
#     serializer_class = WorkerProfileSerializer
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def get(self, request):
#         user = request.user

#         # 🔹 Worker → own profile only
#         if user.role == "worker":
#             profile = get_object_or_404(WorkerProfile, user=user)
#             return Response(self.get_serializer(profile).data)

#         # 🔹 PRO Landscaper only
#         if user.role == "landscaper" and is_pro_landscaper(user):
#             worker_id = request.query_params.get("worker_id")

#             accepted_invitations = TeamInvitation.objects.filter(
#                 landscaper=user.landscaper_profile,
#                 status=InvitationStatus.ACCEPTED
#             )

#             if worker_id:
#                 profile = get_object_or_404(
#                     WorkerProfile,
#                     id=worker_id,
#                     pro_landscaper__in=accepted_invitations
#                 )
#                 return Response(self.get_serializer(profile).data)

#             profiles = WorkerProfile.objects.filter(
#                 Q(pro_landscaper__in=accepted_invitations) |
#                 Q(user=user)
#             )
#             return Response(self.get_serializer(profiles, many=True).data)

#         raise PermissionDenied("Only PRO landscapers are allowed")

#     # ✅ UPDATE
#     def patch(self, request):
#         return self._update_self_profile(request)

#     def put(self, request):
#         return self._update_self_profile(request)

#     def _update_self_profile(self, request):
#         user = request.user

#         if user.role == "worker":
#             profile = get_object_or_404(WorkerProfile, user=user)

#         elif user.role == "landscaper" and is_pro_landscaper(user):
#             profile = get_object_or_404(WorkerProfile, user=user)

#         else:
#             raise PermissionDenied("Only PRO landscapers can update profile")

#         serializer = self.get_serializer(
#             profile,
#             data=request.data,
#             partial=True
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(serializer.data)


# pro landscaper 
class ProLandscaperWorkersView(generics.ListAPIView):
    """
    View for landscaper to see all their workers + self
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAuthenticated, IsLandscaper] 
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user

        if user.role != "landscaper":
            raise PermissionDenied("Only Pro landscapers")

        # Get accepted invitations
        accepted_invitations = TeamInvitation.objects.filter(
            landscaper=user.landscaper_profile,
            status=InvitationStatus.ACCEPTED
        )

        # Return all workers + landscaper's own profile
        return WorkerProfile.objects.filter(
            Q(pro_landscaper__in=accepted_invitations) | Q(user=user)
        )




# client profile views
class ClientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClient]  # 
    parser_classes = [MultiPartParser, FormParser]    # 

    def get_object(self):
        profile, created = ClientProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

        return profile



# ---------------------- Change Password for---------------------- #

# admin change password
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, serializer.instance)
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

# landscaper change password
class ChangePasswordLandscaperView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated, IsLandscaper] 

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, serializer.instance)
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


# Client Change password
class ChangePasswordClientView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    
    permission_classes = [IsAuthenticated,IsClient]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, serializer.instance)
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


class ChangePasswordWorkerView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    
    permission_classes = [IsAuthenticated,IsWorker]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        update_session_auth_hash(request, serializer.instance)
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)