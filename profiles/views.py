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
# search by kim
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Avg
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from message.models import ChatThread
from .models import ClientProfile
from .serializers import ClientProfileSerializer
from accounts.models import User
from accounts.enums import RoleChoices
from profiles.models import LandscaperProfilies
from reviews.models import LandscaperReview
from connections.models import ConnectionRequest
from profiles.serializers import LandscaperProfileSerializer
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer
from django.db.models import F, FloatField, Q, ExpressionWrapper
from django.db.models.functions import ACos, Cos, Sin, Radians


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

# prolandscaer profile views

class ProLandScaperProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated, IsProOrBasicLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=self.request.user)
        return profile



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

# search landscaers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, F
from django.db.models.functions import ACos, Cos, Sin, Radians

from accounts.models import User
from accounts.enums import RoleChoices
from profiles.serializers import LandscaperProfileSerializer

class LandscaperSearchByKMAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        try:
            user_lat = request.GET.get("lat")
            user_lng = request.GET.get("lng")
            km = float(request.GET.get("km", 10))
            min_rating = float(request.GET.get("min_rating", 0))
        except ValueError:
            return Response(
                {"error": "lat, lng, km, and min_rating must be valid numbers"},
                status=400
            )

        landscapers = User.objects.filter(role=RoleChoices.LANDSCAPER)

        # Filter by search query
        if q:
            landscapers = landscapers.filter(
                Q(name__icontains=q) | Q(email__icontains=q)
            )

        # Filter by min rating
        if min_rating > 0:
            landscapers = landscapers.annotate(
                avg_rating=Avg("received_reviews__rating")  # ✅ correct related_name
            ).filter(avg_rating__gte=min_rating)

        # Filter by distance if lat/lng provided
        if user_lat and user_lng:
            try:
                user_lat = float(user_lat)
                user_lng = float(user_lng)
            except ValueError:
                return Response(
                    {"error": "lat and lng must be valid numbers"},
                    status=400
                )

            EARTH_RADIUS = 6371  # KM
            landscapers = landscapers.annotate(
                distance=EARTH_RADIUS * ACos(
                    Cos(Radians(user_lat)) *
                    Cos(Radians(F("latitude"))) *
                    Cos(Radians(F("longitude")) - Radians(user_lng)) +
                    Sin(Radians(user_lat)) *
                    Sin(Radians(F("latitude")))
                )
            ).filter(distance__lte=km).order_by("distance")

        # Get profiles
        profiles = [
            u.landscaperprofilies
            for u in landscapers
            if hasattr(u, "landscaperprofilies")
        ]

        serializer = LandscaperProfileSerializer(
            profiles,
            many=True,
            context={"request": request}
        )

        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        })


# client search views
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.permissions import IsAuthenticated

class ClientSearchByKMAPIView(APIView):
    """
    Search clients by:
    - Name/email (q)
    - Distance from lat/lng within km
    Always includes 'address', 'latitude', 'longitude' in response
    """
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.GET.get("q", "").strip()
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        km = request.GET.get("km", 10)  # default 10 km

        try:
            km = float(km)
        except ValueError:
            return Response({"error": "km must be a valid number"}, status=400)

        clients = User.objects.filter(role="client")

        # Filter by name/email if q provided
        if q:
            clients = clients.filter(Q(name__icontains=q) | Q(email__icontains=q))
    

        # Filter by distance if lat/lng provided
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
            except ValueError:
                return Response({"error": "lat and lng must be valid numbers"}, status=400)

            # Exclude clients without lat/lng
            clients = clients.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

            EARTH_RADIUS = 6371  # km

            distance_expr = ExpressionWrapper(
                EARTH_RADIUS * ACos(
                    Cos(Radians(lat)) *
                    Cos(Radians(F("latitude"))) *
                    Cos(Radians(F("longitude")) - Radians(lng)) +
                    Sin(Radians(lat)) *
                    Sin(Radians(F("latitude")))
                ),
                output_field=FloatField()
            )

            clients = clients.annotate(distance=distance_expr)\
                             .filter(distance__lte=km)\
                             .order_by("distance")

        # Serialize client profiles manually (include address)
        results = []
        for u in clients:
            profile = getattr(u, "clientprofile", None)
            results.append({
                "id": u.id,
                "name": getattr(u, "username", ""),
                "email": u.email,
                "phone": getattr(u, "phone", None),
                "role": u.role,
                "address": getattr(u, "address", None),        # ✅ always include address
                "latitude": float(u.latitude) if u.latitude else None,
                "longitude": float(u.longitude) if u.longitude else None,
                "profile": ClientProfileSerializer(profile, context={"request": request}).data if profile else None
            })

        return Response({
            "count": len(results),
            "results": results
        })


# user list detaisl
class LandscaperDetailWithChatView(generics.RetrieveAPIView):
    """
    Returns detailed landscaper info including:
    - Services, working hours, reviews
    - Message info (chat thread id if exists)
    """
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"  

    def get_object(self):
        landscaper_id = self.kwargs.get("id")
        return get_object_or_404(LandscaperProfilies, id=landscaper_id)

    def get(self, request, *args, **kwargs):
        landscaper = self.get_object()
        serializer = self.get_serializer(landscaper, context={"request": request})
        data = serializer.data

        # Message / chat info
        client = request.user
        landscaper_user = landscaper.user

        thread = ChatThread.objects.filter(
            Q(client=client, landscaper=landscaper_user) |
            Q(client=landscaper_user, landscaper=client)
        ).first()

        data["message_info"] = {
            "can_message": True, 
            "thread_id": thread.id if thread else None
        }

        return Response(data, status=status.HTTP_200_OK)



# client details
class ClientDetailWithChatView(generics.RetrieveAPIView):
    """
    Returns detailed client info including:
    - Services, properties
    - Message info (chat thread with landscaper if exists)
    """
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"  # provide client profile id in URL

    def get_object(self):
        client_id = self.kwargs.get("id")
        return get_object_or_404(ClientProfile, id=client_id)

    def get(self, request, *args, **kwargs):
        client_profile = self.get_object()
        serializer = self.get_serializer(client_profile, context={"request": request})
        data = serializer.data

        # Optional: if logged-in user is a landscaper, check chat thread
        if request.user.role == "landscaper":
            landscaper_user = request.user
            client_user = client_profile.user
            thread = ChatThread.objects.filter(
                Q(client=client_user, landscaper=landscaper_user) |
                Q(client=landscaper_user, landscaper=client_user)
            ).first()
            data["message_info"] = {
                "can_message": True,
                "thread_id": thread.id if thread else None
            }
        else:
            # client viewing another client (optional)
            data["message_info"] = None

        return Response(data, status=status.HTTP_200_OK)
