
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
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import F, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians, Cast
from rest_framework.permissions import IsAuthenticated
from landscapers .models import BusinessProfile

# search by kim
from rest_framework.views import APIView
from django.db.models import F, Avg
from .serializers import LandscaperReminderSerializer, ClientReminderSerializer

from django.db.models import Q
from rest_framework import status
from message.models import ChatThread
from .models import ClientProfile
from .serializers import ClientProfileSerializer
from accounts.models import User
from accounts.enums import RoleChoices
from profiles.models import LandscaperProfilies
from reviews.models import LandscaperReview
from connections.models import ConnectionRequest
from profiles.serializers import LandscaperProfileSerializer,LandscaperPersonalProfileSerializer
from rest_framework import generics, permissions, status
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer
from django.db.models import F, FloatField, Q, ExpressionWrapper
from django.db.models.functions import ACos, Cos, Sin, Radians
from rest_framework.views import APIView
from django.db.models import Q, Avg, F
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsLandscaper
from subscriptions.models import Subscription
from subscriptions.enums import SubscriptionStatus
from django.db.models import OuterRef, Subquery
from django.db.models import F, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians
from common.permissions import IsLandscaper
from django.db.models import Q
from django.db.models import Exists
from rest_framework import generics, permissions
from django.db.models import Exists, OuterRef
from landscapers.models import BusinessProfile
from subscriptions.models import Subscription, SubscriptionStatus
from .serializers import LandscaperProfileSerializer





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
# class LandScaperProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = LandscaperProfileSerializer
#     permission_classes = [IsAuthenticated, IsLandscaper]

#     def get_object(self):
#         profile, created = BusinessProfile.objects.get_or_create(
#             user=self.request.user
#         )
#         return profile





class LandScaperProfileView(generics.RetrieveAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get_object(self):
        return BusinessProfile.objects.get(user=self.request.user)




class LandscaperPersonalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LandscaperPersonalProfileSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = LandscaperProfilies.objects.get_or_create(user=self.request.user)
        return profile







class ClientProfileView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    def get_object(self, user):
        # Get or create client profile
        profile, created = ClientProfile.objects.get_or_create(user=user)
        return profile

    # ---------------- GET profile ----------------
    def get(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(client_profile, context={"request": request})
        return Response(serializer.data, status=200)

    # ---------------- PUT (full update) ----------------
    def put(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(client_profile, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    # ---------------- PATCH (partial update) ----------------
    def patch(self, request):
        client_profile = self.get_object(request.user)
        serializer = ClientProfileSerializer(client_profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)


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



# # ---------------- All Landscapers ----------------

from django.db.models import Exists, OuterRef, Prefetch
from landscapers.models import Service, WorkingHours
from reviews.models import LandscaperReview

class AllLandscapersListView(generics.ListAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        active_sub = Subscription.objects.filter(
            user=OuterRef("user"),
            is_active=True,
            status=SubscriptionStatus.ACTIVE
        )


        services_qs = Service.objects.only(
            "id", "name", "pricing_type", "base_price", "business_id"
        ).order_by("-id")

        working_hours_qs = WorkingHours.objects.only(
            "id", "day", "start_time", "end_time"
        ).order_by("-id")

        reviews_qs = LandscaperReview.objects.only(
            "id", "rating", "comment", "client_id", "created_at", "landscaper_id"
        ).order_by("-created_at")

        return BusinessProfile.objects.annotate(
            has_active_sub=Exists(active_sub)
            
        ).select_related(
            "user"
        ).prefetch_related(

            Prefetch(
                "services",
                queryset=services_qs,
                to_attr="pref_services"
            ),

            Prefetch(
                "working_hours",
                queryset=working_hours_qs,
                to_attr="pref_working_hours"
            ),

            Prefetch(
                "user__received_reviews",
                queryset=reviews_qs,
                to_attr="pref_received_reviews"
            ),
        ).order_by("-id")

        

# ---------------- All Clients ----------------


class ClientProfileListView(generics.ListAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ClientProfile.objects.select_related("user")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        connections = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        )

        connection_map = {}
        for conn in connections:
            other_id = conn.receiver.id if conn.sender == request.user else conn.sender.id
            connection_map[other_id] = conn

        response_data = []

        for client in queryset:
            user_obj = client.user
            conn = connection_map.get(user_obj.id)

            status = "none"

            if conn:
                if conn.is_accepted is None:
                    status = "pending_sent" if conn.sender == request.user else "pending_received"
                elif conn.is_accepted is True:
                    status = "accepted"
                elif conn.is_accepted is False:
                    status = "rejected"

            serialized = self.get_serializer(client).data
            serialized["connection_status"] = status

            response_data.append(serialized)

        return Response(response_data)



class ClientDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single client profile by USER ID (recommended)
    Includes:
    - profile data
    - optional chat thread info for landscaper
    """

    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            user_id = self.kwargs.get("id")

            if not user_id:
                raise ValueError("User ID is required in URL")

            # SAFE FETCH: ensure profile exists for user
            profile = get_object_or_404(
                ClientProfile.objects.select_related("user"),
                user__id=user_id
            )

            return profile

        except ValueError as e:
            # bad request (missing id)
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": str(e)})

        except Exception:
            # unexpected server issue
            from rest_framework.exceptions import NotFound
            raise NotFound({"detail": "Client profile not found"})

    def retrieve(self, request, *args, **kwargs):
        try:
            client_profile = self.get_object()

            serializer = self.get_serializer(
                client_profile,
                context={"request": request}
            )
            data = serializer.data

            # ---------------- CHAT LOGIC ----------------
            data["message_info"] = None

            if hasattr(request.user, "role") and request.user.role == "landscaper":
                thread = ChatThread.objects.filter(
                    Q(client=client_profile.user, landscaper=request.user) |
                    Q(client=request.user, landscaper=client_profile.user)
                ).first()

                data["message_info"] = {
                    "can_message": True,
                    "thread_id": thread.id if thread else None
                }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "detail": "Something went wrong while fetching client profile",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# profiles/views.py
from rest_framework import generics, permissions
from django.db.models import Q, F, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians, Cast
from django.db.models import Avg
from profiles.models import LandscaperProfilies
from profiles.serializers import LandscaperProfileSerializer

class LandscaperSearchByKMAPIView(generics.ListAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = LandscaperProfilies.objects.all()
        request = self.request
        q = request.GET.get("q", "").strip()
        min_rating = request.GET.get("min_rating")
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        km = request.GET.get("km", 10)

        # Filter by name/email
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(user__email__icontains=q)
            )

        # Filter by min_rating
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.annotate(
                    avg_rating=Avg("user__received_reviews__rating")
                ).filter(avg_rating__gte=min_rating)
            except ValueError:
                pass

        # Filter by distance if lat/lng provided
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                km = float(km)
                EARTH_RADIUS = 6371

                queryset = queryset.annotate(
                    distance=EARTH_RADIUS * ACos(
                        Cos(Radians(lat)) *
                        Cos(Radians(Cast(F("user__landscaper_profile__latitude"), FloatField()))) *
                        Cos(Radians(Cast(F("user__landscaper_profile__longitude"), FloatField())) - Radians(lng)) +
                        Sin(Radians(lat)) *
                        Sin(Radians(Cast(F("user__landscaper_profile__latitude"), FloatField())))
                    )
                ).filter(distance__lte=km).order_by("distance")

            except ValueError:
                pass

        return queryset.distinct()



# client search views
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
# class LandscaperDetailWithChatView(generics.RetrieveAPIView):
#     """
#     Returns detailed landscaper info including:
#     - Services, working hours, reviews
#     - Message info (chat thread id if exists)
#     """
#     serializer_class = LandscaperProfileSerializer
#     permission_classes = [IsAuthenticated]
#     lookup_field = "id"  

#     def get_object(self):
#         landscaper_id = self.kwargs.get("id")
#         return get_object_or_404(LandscaperProfilies, id=landscaper_id)

#     def get(self, request, *args, **kwargs):
#         landscaper = self.get_object()
#         serializer = self.get_serializer(landscaper, context={"request": request})
#         data = serializer.data

#         # Message / chat info
#         client = request.user
#         landscaper_user = landscaper.user

#         thread = ChatThread.objects.filter(
#             Q(client=client, landscaper=landscaper_user) |
#             Q(client=landscaper_user, landscaper=client)
#         ).first()

#         data["message_info"] = {
#             "can_message": True, 
#             "thread_id": thread.id if thread else None
#         }

#         return Response(data, status=status.HTTP_200_OK)

class LandscaperDetailWithChatView(generics.RetrieveAPIView):
    serializer_class = LandscaperProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # IMPORTANT: use BusinessProfile ONLY
        landscaper_id = self.kwargs.get("id")

        return get_object_or_404(
            BusinessProfile.objects.select_related("user"),
            id=landscaper_id
        )

    def get(self, request, *args, **kwargs):
        landscaper = self.get_object()

        serializer = self.get_serializer(
            landscaper,
            context={"request": request}
        )

        data = serializer.data

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
# class ClientDetailWithChatView(generics.RetrieveAPIView):
#     """
#     Returns detailed client info including:
#     - Services, properties
#     - Message info (chat thread with landscaper if exists)
#     """
#     serializer_class = ClientProfileSerializer
#     permission_classes = [IsAuthenticated]
#     lookup_field = "id"  # provide client profile id in URL

#     def get_object(self):
#         client_id = self.kwargs.get("id")
#         return get_object_or_404(ClientProfile, id=client_id)

#     def get(self, request, *args, **kwargs):
#         client_profile = self.get_object()
#         serializer = self.get_serializer(client_profile, context={"request": request})
#         data = serializer.data

#         # Optional: if logged-in user is a landscaper, check chat thread
#         if request.user.role == "landscaper":
#             landscaper_user = request.user
#             client_user = client_profile.user
#             thread = ChatThread.objects.filter(
#                 Q(client=client_user, landscaper=landscaper_user) |
#                 Q(client=landscaper_user, landscaper=client_user)
#             ).first()
#             data["message_info"] = {
#                 "can_message": True,
#                 "thread_id": thread.id if thread else None
#             }
#         else:
#             # client viewing another client (optional)
#             data["message_info"] = None

#         return Response(data, status=status.HTTP_200_OK)

class ClientDetailWithChatView(generics.RetrieveAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = ClientProfile.objects.all()
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        client_profile = self.get_object()
        serializer = self.get_serializer(client_profile, context={"request": request})
        data = serializer.data

        if request.user.role == "landscaper":
            thread = ChatThread.objects.filter(
                Q(client=client_profile.user, landscaper=request.user) |
                Q(client=request.user, landscaper=client_profile.user)
            ).first()

            data["message_info"] = {
                "can_message": True,
                "thread_id": thread.id if thread else None
            }
        else:
            data["message_info"] = None

        return Response(data)

# reminder views
# profiles/views.py

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class ReminderToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        job_reminder = request.data.get("job_reminder_enabled")
        service_reminder = request.data.get("service_reminder_enabled")

        if hasattr(user, "landscaperprofilies"):
            profile = user.landscaperprofilies
            if job_reminder is not None:
                profile.job_reminder_enabled = job_reminder
                profile.save(update_fields=["job_reminder_enabled"])
                return Response({
                    "job_reminder_enabled": profile.job_reminder_enabled
                })

        elif hasattr(user, "clientprofile"):
            profile = user.clientprofile
            if service_reminder is not None:
                profile.service_reminder_enabled = service_reminder
                profile.save(update_fields=["service_reminder_enabled"])
                return Response({
                    "service_reminder_enabled": profile.service_reminder_enabled
                })

        return Response(
            {"detail": "Invalid request"},
            status=status.HTTP_400_BAD_REQUEST
        )





class LandscaperReminderToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        landscaper = getattr(request.user, "landscaperprofilies", None)
        if not landscaper:
            return Response({"detail": "User is not a landscaper"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LandscaperReminderSerializer(landscaper)
        return Response(serializer.data)

    def patch(self, request):
        landscaper = getattr(request.user, "landscaperprofilies", None)
        if not landscaper:
            return Response({"detail": "User is not a landscaper"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LandscaperReminderSerializer(landscaper, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClientReminderToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = getattr(request.user, "clientprofile", None)
        if not client:
            return Response({"detail": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientReminderSerializer(client)
        return Response(serializer.data)

    def patch(self, request):
        client = getattr(request.user, "clientprofile", None)
        if not client:
            return Response({"detail": "User is not a client"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClientReminderSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# external client views
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from profiles.models import ExternalClient
from profiles.serializers import ExternalClientSerializer


class ExternalClientListCreateView(generics.ListCreateAPIView):
    serializer_class = ExternalClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return ExternalClient.objects.none()

        queryset = ExternalClient.objects.filter(landscaper=landscaper)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            raise PermissionDenied("Landscaper profile not found.")

        serializer.save(landscaper=landscaper)


class ExternalClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExternalClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return ExternalClient.objects.none()

        return ExternalClient.objects.filter(landscaper=landscaper)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Soft delete instead of hard delete
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

        return Response(
            {"message": "External client deactivated successfully."},
            status=status.HTTP_200_OK
        )

class ExternalClientReactivateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        landscaper = getattr(request.user, "landscaper_profile", None)
        if not landscaper:
            return Response(
                {"error": "Landscaper profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            client = ExternalClient.objects.get(id=pk, landscaper=landscaper)
        except ExternalClient.DoesNotExist:
            return Response(
                {"error": "External client not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        client.is_active = True
        client.save(update_fields=["is_active", "updated_at"])

        return Response(
            {"message": "External client reactivated successfully."},
            status=status.HTTP_200_OK
        )