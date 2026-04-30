
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
from common.permissions import IsClient, IsLandscaper
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView

from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
from profiles.models import LandscaperProfilies, ClientProfile
from reviews.models import LandscaperReview
from subscriptions.models import Subscription
from property.models import Property
from accounts.models import User
from connections.models import ConnectionRequest
from connections.serializers import (
    ConnectionRequestDetailSerializer,
    SendConnectionRequestSerializer,
    RespondConnectionRequestSerializer,
    AcceptedConnectionSerializer,
    ConnectedUserSerializer,
)

from landscapers.models import BusinessProfile, Service
from landscapers.serializers import (
    BusinessLandscaperProfileSerializer,
    # LandscaperProfileSerializer,
)
from profiles.models import ClientProfile, LandscaperProfilies
from services.models import ClientService
from profiles.serializers import ClientProfileSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from jobs.models import Job
from subscriptions.models import Subscription, SubscriptionStatus
from django.db import transaction

from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from connections.models import ConnectionRequest

User = get_user_model()





class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        receiver = User.objects.get(id=serializer.validated_data["receiver_id"])

        connection = ConnectionRequest.objects.create(
            sender=request.user,
            receiver=receiver
        )

        return Response(
            {
                "connection_id": connection.id,
                "receiver_profile": self._get_profile(receiver, request),
            },
            status=status.HTTP_201_CREATED
        )

    def _get_profile(self, user, request):
        business_profile = getattr(user, "landscaper_profile", None)
        if business_profile:
            data = BusinessLandscaperProfileSerializer(
                business_profile,
                context={"request": request}
            ).data
            data["user_id"] = user.id
            data["email"] = user.email
            data["type"] = "landscaper_business"
            return data

        basic_profile = getattr(user, "landscaperprofilies", None)
        if basic_profile:
            return {
                "user_id": user.id,
                "name": basic_profile.name,
                "phone": basic_profile.phone,
                "image": basic_profile.image.url if basic_profile.image else None,
                "type": "landscaper_basic",
            }

        client_profile = getattr(user, "client_profile", None)
        if client_profile:
            data = ClientProfileSerializer(
                client_profile,
                context={"request": request}
            ).data
            data["type"] = "client"
            return data

        return {
            "user_id": user.id,
            "email": user.email,
            "type": "unknown",
        }


class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_requests = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted__isnull=True
        ).select_related("sender", "receiver").order_by("-created_at")

        response = []

        for req in pending_requests:
            sender = req.sender
            sender_data = {"user_id": sender.id, "email": sender.email, "type": "unknown"}

            business_profile = getattr(sender, "landscaper_profile", None)
            basic_profile = getattr(sender, "landscaperprofilies", None)
            client_profile = getattr(sender, "client_profile", None)

            if business_profile:
                sender_data = LandscaperProfileSerializer(
                    business_profile,
                    context={"request": request}
                ).data
                sender_data["type"] = "landscaper"
            elif basic_profile:
                sender_data = {
                    "user_id": sender.id,
                    "name": basic_profile.name,
                    "phone": basic_profile.phone,
                    "image": basic_profile.image.url if basic_profile.image else None,
                    "type": "landscaper_basic",
                }
            elif client_profile:
                sender_data = ClientProfileSerializer(
                    client_profile,
                    context={"request": request}
                ).data
                sender_data["type"] = "client"

            delta = now() - req.created_at
            if delta < timedelta(minutes=1):
                sent_since = "just now"
            elif delta < timedelta(hours=1):
                minutes = int(delta.total_seconds() // 60)
                sent_since = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif delta < timedelta(days=1):
                hours = int(delta.total_seconds() // 3600)
                sent_since = f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif delta < timedelta(days=7):
                days = delta.days
                sent_since = f"{days} day{'s' if days != 1 else ''} ago"
            else:
                sent_since = req.created_at.strftime("%Y-%m-%d")

            response.append({
                "connection_id": req.id,
                "sent_by": sender_data,
                "created_at": req.created_at,
                "sent_since": sent_since,
                "status": "pending",
            })

        return Response(response, status=status.HTTP_200_OK)


class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        return Response(
            ConnectionRequestDetailSerializer(
                qs,
                many=True,
                context={"request": request}
            ).data
        )


class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        connection = get_object_or_404(ConnectionRequest, id=pk)

        # -------------------------
        # Already handled
        # -------------------------
        if connection.is_accepted is not None:
            return Response(
                {"detail": "Already responded."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user not in (connection.sender, connection.receiver):
            return Response(
                {"detail": "Not allowed."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RespondConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        sender = connection.sender
        receiver = connection.receiver

        # -------------------------
        # Identify roles
        # -------------------------
        if sender.role == "client" and receiver.role == "landscaper":
            client_user = sender
            landscaper_user = receiver
        elif sender.role == "landscaper" and receiver.role == "client":
            client_user = receiver
            landscaper_user = sender
        else:
            return Response(
                {"detail": "Invalid connection type."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------
        # Profiles
        # -------------------------
        client_profile = ClientProfile.objects.filter(user=client_user).first()
        landscaper_business = BusinessProfile.objects.filter(user=landscaper_user).first()
        landscaper_basic = LandscaperProfilies.objects.filter(user=landscaper_user).first()

        if not client_profile:
            return Response({"detail": "Client profile missing"}, status=400)

        if not landscaper_business:
            return Response({"detail": "Business profile missing"}, status=400)

        if not landscaper_basic:
            return Response({"detail": "Basic profile missing"}, status=400)

        # -------------------------
        # REJECT
        # -------------------------
        if action == "reject":
            connection.is_accepted = False
            connection.save()

            return Response({
                "connection_id": connection.id,
                "status": "rejected",
                "client": ClientProfileSerializer(client_profile).data,
                "landscaper": LandscaperProfileSerializer(landscaper_business).data
            })

        # -------------------------
        # CHECK PLAN LIMIT
        # -------------------------
        accepted_count = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=landscaper_user) | Q(receiver=landscaper_user)
        ).count()

        plan_name = "basic"

        subscription = Subscription.objects.filter(
            user=landscaper_user,
            is_active=True,
            status__in=[
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING  
            ]
        ).select_related("plan").order_by("-end_date").first()

        # determine plan
        if subscription and subscription.plan:
            plan_name = subscription.plan.name.lower()
        elif landscaper_basic and landscaper_basic.plan:
            plan_name = landscaper_basic.plan.name.lower()
        else:
            plan_name = "basic"

        # -------------------------
        # ACCEPT CONNECTION ONLY
        # -------------------------
        connection.is_accepted = True
        connection.save()

        # client can have only 1 landscaper
        if user.role == "client":
            ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=client_user) | Q(receiver=client_user)
            ).exclude(id=connection.id).delete()

        # -------------------------
        # GET SERVICES (IMPORTANT)
        # -------------------------
        services = Service.objects.filter(
            business=landscaper_business,
            is_active=True
        )

        service_data = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "price": float(s.base_price or 0),
                "pricing_type": s.pricing_type,
            }
            for s in services
        ]

        # -------------------------
        # FINAL RESPONSE ✅ CLEAN
        # -------------------------
        return Response({
            "connection_id": connection.id,
            "status": "accepted",
            "accepted_by": user.role,

            "client": {
                "id": client_user.id,
                "name": client_profile.name,
                "email": client_user.email,
            },

            "landscaper": {
                "id": landscaper_user.id,
                "business_name": landscaper_business.business_name,
                "email": landscaper_user.email,
            },

            "services": service_data,

            "connection_limits": {
                "plan": plan_name,
                "accepted_connections": accepted_count + 1,
                "remaining_slots": None if plan_name != "basic" else max(0, 10 - (accepted_count + 1)),
            }

        }, status=status.HTTP_200_OK)




class CancelConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            connection = ConnectionRequest.objects.get(
                id=pk,
                sender=request.user,
                is_accepted__isnull=True
            )
        except ConnectionRequest.DoesNotExist:
            return Response(
                {"error": "Request not found or cannot be cancelled"},
                status=status.HTTP_404_NOT_FOUND
            )

        connection.delete()
        return Response(
            {"message": "Request cancelled successfully"},
            status=status.HTTP_200_OK
        )





class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # -----------------------------
    # TIME AGO
    # -----------------------------
    def get_connected_since(self, created_at):
        try:
            diff = timezone.now() - created_at

            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"

            hours = diff.seconds // 3600
            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} ago"

            minutes = diff.seconds // 60
            if minutes > 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

            return "just now"

        except Exception:
            return "unknown"

    # -----------------------------
    # RATING (SAFE)
    # -----------------------------
    def get_rating(self, user):
        try:
            avg = LandscaperReview.objects.filter(
                landscaper=user
            ).aggregate(avg=models.Avg("rating"))["avg"]
            return round(avg, 1) if avg else 0
        except Exception:
            return 0

    # -----------------------------
    # PROFILE RESOLVER (FIXED - NO MODEL CRASH)
    # -----------------------------
    def get_profile_data(self, user, request):

        # ---------------- LANDSCAPER BUSINESS ----------------
        business = BusinessProfile.objects.filter(user=user).first()

        if business:
            return {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "type": "landscaper",

                "business_name": business.business_name,
                "business_email": business.business_email,
                "business_phone": business.business_phone,

                # ONLY business location here
                "business_address": {
                    "latitude": business.latitude,
                    "longitude": business.longitude,
                },

                # USER ADDRESS (from accounts.User)
                "user_address": {
                    "address": user.address,
                    "latitude": user.latitude,
                    "longitude": user.longitude,
                },

                "profile_image": getattr(business.profile_image, "url", None),
                "rating": self.get_rating(user),
            }

        # ---------------- LANDSCAPER BASIC PROFILE ----------------
        landscaper_basic = getattr(user, "landscaperprofilies", None)

        if landscaper_basic:
            return {
                "user_id": user.id,
                "name": landscaper_basic.name,
                "email": user.email,
                "role": user.role,
                "type": "landscaper",

                # USER ADDRESS ONLY
                "user_address": {
                    "address": user.address,
                    "latitude": user.latitude,
                    "longitude": user.longitude,
                },

                "profile_image": getattr(landscaper_basic.image, "url", None),
                "rating": self.get_rating(user),
            }

        # ---------------- CLIENT PROFILE ----------------

        client = getattr(user, "clientprofile", None)

        if client:
            properties = Property.objects.filter(owner=user)

            return {
                "user_id": user.id,
                "name": client.name,
                "email": user.email,
                "role": user.role,
                "type": "client",

                # USER ADDRESS ONLY
                "user_address": {
                    "address": user.address,
                    "latitude": user.latitude,
                    "longitude": user.longitude,
                },

                "profile_image": getattr(client.image, "url", None),
                "rating": self.get_rating(user),

                # ✅ ACTIVE PROPERTIES
                "properties": [
                    {
                        "id": p.id,
                        "address": p.address,
                        "latitude": p.latitude,
                        "longitude": p.longitude,
                        "property_size": p.property_size,
                        "cut_height_inches": p.cut_height_inches,
                        "grass_types": p.grass_types,
                        "notes": p.notes,
                        "images": p.images,
                    }
                    for p in properties
                ]
            }
        # ---------------- FALLBACK ----------------
        return {
            "user_id": user.id,
            "name": getattr(user, "name", ""),
            "email": user.email,
            "role": getattr(user, "role", None),
            "type": "unknown",

            "user_address": {
                "address": user.address,
                "latitude": user.latitude,
                "longitude": user.longitude,
            },

            "profile_image": None,
            "rating": self.get_rating(user),
        }

    # -----------------------------
    # CONNECTION LIMITS (UNCHANGED)
    # -----------------------------
    def get_connection_limits(self, user, count):

        subscription = Subscription.objects.filter(
            user=user,
            is_active=True
        ).select_related("plan").order_by("-end_date").first()

        plan_name = subscription.plan.name.lower() if subscription and subscription.plan else "basic"

        if plan_name in ["pro", "premium", "trial"]:
            return {
                "plan": "pro",
                "accepted_connections": count,
                "max_connections": "unlimited",
                "remaining_slots": "unlimited",
            }

        max_connections = 10

        return {
            "plan": "basic",
            "accepted_connections": count,
            "max_connections": max_connections,
            "remaining_slots": max(0, max_connections - count),
        }

    # -----------------------------
    # MAIN API (NO RESPONSE CHANGE)
    # -----------------------------
    def get(self, request):

        user = request.user

        connections_qs = ConnectionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_accepted=True
        ).select_related("sender", "receiver").order_by("-created_at")

        connections_data = []

        for conn in connections_qs:

            other_user = conn.receiver if conn.sender == user else conn.sender

            connections_data.append({
                "connection_request_id": conn.id,
                "connected_user": {
                    "id": other_user.id,
                    "name": getattr(other_user, "name", ""),
                    "email": other_user.email,
                    "role": getattr(other_user, "role", ""),
                },
                "profile": self.get_profile_data(other_user, request),
                "connected_at": conn.created_at,
                "connected_since": self.get_connected_since(conn.created_at),
                "upcoming_job": None,
            })

        return Response({
            "count": connections_qs.count(),
            "connections": connections_data,
            "connection_limits": self.get_connection_limits(user, connections_qs.count()),
        }, status=status.HTTP_200_OK)



class RemoveConnectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, connection_id):
        connection = get_object_or_404(ConnectionRequest, id=connection_id)

        if request.user not in [connection.sender, connection.receiver]:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        connection.delete()
        return Response(
            {"message": "Connection removed"},
            status=status.HTTP_200_OK
        )


        

class ConnectedClientListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get(self, request):
        user = request.user
        search_query = request.GET.get("search", "").strip()

        connections = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related("sender", "receiver")

        if search_query:
            connections = connections.filter(
                Q(sender__name__icontains=search_query) |
                Q(sender__email__icontains=search_query) |
                Q(receiver__name__icontains=search_query) |
                Q(receiver__email__icontains=search_query)
            )

        clients_data = []

        for conn in connections:
            other_user = conn.receiver if conn.sender == user else conn.sender
            client_profile = ClientProfile.objects.filter(user=other_user).first()

            if not client_profile:
                continue

            clients_data.append({
                "connection_id": conn.id,
                "client_id": other_user.id,
                "name": getattr(other_user, "name", ""),
                "profile_image": client_profile.image.url if client_profile.image else None,
                "email": other_user.email,
                "phone": getattr(client_profile, "phone", ""),
                "address": getattr(client_profile, "address", None),
                "latitude": getattr(client_profile, "latitude", None),
                "longitude": getattr(client_profile, "longitude", None),
                "connected_at": conn.created_at,
            })

        return Response(
            {
                "count": len(clients_data),
                "clients": clients_data,
            },
            status=status.HTTP_200_OK
        )

