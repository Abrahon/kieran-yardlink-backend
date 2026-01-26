from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import AdminProfile
from .models import WorkerProfile
from .models import ClientProfile
from .serializers import AdminProfileSerializer,ChangePasswordSerializer,WorkerProfileSerializer,ClientProfileSerializer,LandscaperProfileSerializer
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
from invitations.permissions import IsProLandscaper, IsProOrBasicLandscaper

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer


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


# pro landscaper 
class ProLandscaperWorkersView(generics.ListAPIView):
    """
    View for landscaper to see all their workers + self
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAuthenticated, IsProLandscaper] 
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




# prolandscaer profile views
from profiles.models import LandscaperProfilies

class ProLandScaperProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated, IsProOrBasicLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, created = LandscaperProfilies.objects.get_or_create(
            user=self.request.user
        )
        return profile






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ClientProfile
from .serializers import ClientProfileSerializer

# If you have a custom permission for client users
try:
    from .permissions import IsClient
except ImportError:
    IsClient = IsAuthenticated  # fallback if not created yet



class ClientProfileView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    def get_object(self, user):
        # Get or create client profile
        profile, created = ClientProfile.objects.get_or_create(user=user)
        return profile

    # ---------------- GET profile ----------------
    def get(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(client_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ---------------- PUT (full update) ----------------
    def put(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(
            client_profile,
            data=request.data  # all required fields must be sent
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ---------------- PATCH (partial update) ----------------
    def patch(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(
            client_profile,
            data=request.data,
            partial=True  # only fields you want to change
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class ChangePasswordAPIView(generics.UpdateAPIView):
    """
    Allows any authenticated user (Admin, Client, Landscaper, Worker)
    to change their own password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]  # any logged-in user

    def get_object(self):
        return self.request.user  # always self

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(
            instance=user,
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Keeps the user logged in after password change
        update_session_auth_hash(request, serializer.instance)

        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )


from .models import LandscaperProfilies

# ---------------- All Landscapers ----------------

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import LandscaperProfilies
from .serializers import LandscaperProfileSerializer

class AllLandscapersListView(generics.ListAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated]
    # pagination_class = None  # no pagination

    def get_queryset(self):
        return (
            LandscaperProfilies.objects
            .select_related("user")
            .all()
        )






# ---------------- All Clients ----------------
class ClientProfileListView(generics.ListAPIView):
    queryset = ClientProfile.objects.all()
    print("queryset",queryset)
    serializer_class = ClientProfileSerializer
