
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

from jobs.models import Job
from subscriptions.models import Subscription, SubscriptionStatus
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
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
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


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
                SubscriptionStatus.TRIALING   # ✅ THIS IS THE KEY FIX
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


# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         current_time = timezone.now()

#         connections = ConnectionRequest.objects.filter(
#             Q(sender=user) | Q(receiver=user),
#             is_accepted=True
#         ).select_related(
#             "sender", "receiver", "schedule"
#         ).order_by("-created_at")

#         response_data = []

#         for conn in connections:
#             other_user = conn.receiver if conn.sender == user else conn.sender

#             diff = current_time - conn.created_at
#             if diff.days > 0:
#                 connected_since = f"{diff.days} days ago"
#             elif diff.seconds >= 3600:
#                 connected_since = f"{diff.seconds // 3600} hours ago"
#             elif diff.seconds >= 60:
#                 connected_since = f"{diff.seconds // 60} minutes ago"
#             else:
#                 connected_since = "Just now"

#             business_profile = getattr(other_user, "landscaper_profile", None)
#             client_profile = getattr(other_user, "client_profile", None)

#             if business_profile:
#                 role = "landscaper"
#                 profile_data = LandscaperProfileSerializer(
#                     business_profile,
#                     context={"request": request}
#                 ).data
#             elif client_profile:
#                 role = "client"
#                 profile_data = ClientProfileSerializer(
#                     client_profile,
#                     context={"request": request}
#                 ).data
#             else:
#                 continue

#             upcoming_job = None
#             if conn.schedule:
#                 upcoming_job = {
#                     "job_id": conn.schedule.id,
#                     "service_name": getattr(conn.schedule.service, "name", None),
#                     "date": conn.schedule.scheduled_date,
#                     "time": conn.schedule.scheduled_time,
#                     "price": float(getattr(conn.schedule.service, "price", 0) or 0),
#                     "payment_status": conn.schedule.payment_status,
#                 }

#             response_data.append({
#                 "connection_id": conn.id,
#                 "connected_user": {
#                     "id": other_user.id,
#                     "name": getattr(other_user, "name", ""),
#                     "email": other_user.email,
#                     "role": role,
#                 },
#                 "profile": profile_data,
#                 "connected_at": conn.created_at,
#                 "connected_since": connected_since,
#                 "upcoming_job": upcoming_job,
#             })

#         total_connections = len(response_data)

#         first_day_this_month = current_time.replace(day=1)
#         first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
#         last_day_last_month = first_day_this_month - timedelta(days=1)

#         active_users_this_month = ConnectionRequest.objects.filter(
#             is_accepted=True,
#             created_at__gte=first_day_this_month
#         ).values_list("receiver", "sender")

#         active_users_last_month = ConnectionRequest.objects.filter(
#             is_accepted=True,
#             created_at__gte=first_day_last_month,
#             created_at__lte=last_day_last_month
#         ).values_list("receiver", "sender")

#         active_this = set(u for pair in active_users_this_month for u in pair)
#         active_last = set(u for pair in active_users_last_month for u in pair)

#         total_users = User.objects.filter(is_active=True).count()

#         active_percentage = (len(active_this) / total_users * 100) if total_users > 0 else 0
#         previous_month_percentage = (len(active_last) / total_users * 100) if total_users > 0 else 0

#         change_value = active_percentage - previous_month_percentage
#         if change_value > 0:
#             change_vs_last_month = f"+{change_value:.1f}"
#         elif change_value < 0:
#             change_vs_last_month = f"{change_value:.1f}"
#         else:
#             change_vs_last_month = "0.0"

#         connection_limits = None
#         landscaper_business_self = getattr(user, "landscaper_profile", None)
#         landscaper_basic_self = getattr(user, "landscaperprofilies", None)

#         if landscaper_business_self:
#             subscription = Subscription.objects.filter(
#                 user=user,
#                 is_active=True,
#                 status=SubscriptionStatus.ACTIVE
#             ).select_related("plan").first()

#             if subscription and subscription.plan:
#                 plan_name = subscription.plan.name.upper()
#             elif landscaper_basic_self and landscaper_basic_self.plan:
#                 plan_name = landscaper_basic_self.plan.name.upper()
#             else:
#                 plan_name = "BASIC"

#             accepted_count = ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=user) | Q(receiver=user)
#             ).count()

#             if plan_name == "BASIC":
#                 connection_limits = {
#                     "plan": "BASIC",
#                     "accepted_connections": accepted_count,
#                     "max_connections": 10,
#                     "remaining_slots": max(0, 10 - accepted_count),
#                 }
#             else:
#                 connection_limits = {
#                     "plan": plan_name,
#                     "accepted_connections": accepted_count,
#                     "max_connections": None,
#                     "remaining_slots": None,
#                 }

#         return Response(
#             {
#                 "count": total_connections,
#                 "connections": response_data,
#                 "active_percentage": round(active_percentage, 1),
#                 "previous_month_percentage": round(previous_month_percentage, 1),
#                 "change_vs_last_month": change_vs_last_month,
#                 "connection_limits": connection_limits,
#             },
#             status=status.HTTP_200_OK
#         )



from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     # -----------------------------
#     # PROFILE RESOLVER
#     # -----------------------------
#     def get_profile_data(self, user, request):

#         business_profile = getattr(user, "landscaper_profile", None)
#         basic_profile = getattr(user, "landscaperprofilies", None)
#         client_profile = getattr(user, "client_profile", None)

#         if business_profile:
#             data = BusinessLandscaperProfileSerializer(
#                 business_profile,
#                 context={"request": request}
#             ).data
#             data.update({
#                 "user_id": user.id,
#                 "email": user.email,
#                 "type": "landscaper_business"
#             })
#             return data

#         if basic_profile:
#             return {
#                 "user_id": user.id,
#                 "name": getattr(basic_profile, "name", ""),
#                 "phone": getattr(basic_profile, "phone", ""),
#                 "image": getattr(basic_profile.image, "url", None) if basic_profile.image else None,
#                 "type": "landscaper_basic",
#             }

#         if client_profile:
#             data = ClientProfileSerializer(
#                 client_profile,
#                 context={"request": request}
#             ).data
#             data.update({
#                 "user_id": user.id,
#                 "email": user.email,
#                 "type": "client"
#             })
#             return data

#         return {
#             "user_id": user.id,
#             "name": getattr(user, "name", ""),
#             "email": user.email,
#             "type": "unknown",
#         }

#     # -----------------------------
#     # FIXED: TIME AGO FUNCTION (MISSING ERROR FIX)
#     # -----------------------------
#     def get_connected_since(self, created_at):
#         try:
#             diff = timezone.now() - created_at

#             if diff.days > 0:
#                 return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"

#             hours = diff.seconds // 3600
#             if hours > 0:
#                 return f"{hours} hour{'s' if hours != 1 else ''} ago"

#             minutes = diff.seconds // 60
#             if minutes > 0:
#                 return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

#             return "just now"

#         except Exception:
#             return "unknown"

#     # -----------------------------
#     # UPCOMING JOB (FIXED - NO service direct)
#     # -----------------------------
#     def get_upcoming_job(self, conn):
#         try:
#             job = getattr(conn, "schedule", None)
#             if not job:
#                 return None

#             booking = getattr(job, "booking", None)
#             service = getattr(booking, "service", None) if booking else None

#             return {
#                 "job_id": job.id,
#                 "service_name": getattr(service, "name", None),
#                 "date": getattr(job, "scheduled_date", None),
#                 "time": getattr(job, "scheduled_time", None),
#                 "price": float(getattr(service, "price", 0) or 0),
#                 "payment_status": getattr(job, "payment_status", None),
#                 "is_completed": getattr(job, "is_completed", False),
#             }

#         except Exception:
#             return None

#     # -----------------------------
#     # CONNECTION LIMITS (FIXED PLAN PRIORITY)
#     # -----------------------------
#     def get_connection_limits(self, user, accepted_count):

#         subscription = Subscription.objects.filter(
#             user=user,
#             is_active=True
#         ).select_related("plan").order_by("-end_date").first()

#         plan_name = subscription.plan.name.lower() if subscription and subscription.plan else "basic"

#         # ---------------- PRO PLAN ----------------
#         if plan_name in ["pro", "premium", "trialing"]:
#             return {
#                 "plan": "pro",
#                 "accepted_connections": accepted_count,
#                 "max_connections": "unlimited",
#                 "remaining_slots": "unlimited",
#             }

#         # ---------------- BASIC PLAN ----------------
#         max_connections = 10
#         remaining = max(0, max_connections - accepted_count)

#         return {
#             "plan": "basic",
#             "accepted_connections": accepted_count,
#             "max_connections": max_connections,
#             "remaining_slots": remaining,
#         }
        
#     # -----------------------------
#     # MAIN API
#     # -----------------------------
#     def get(self, request):

#         try:
#             user = request.user

#             connections_qs = ConnectionRequest.objects.filter(
#                 Q(sender=user) | Q(receiver=user),
#                 is_accepted=True
#             ).select_related(
#                 "sender",
#                 "receiver",
#                 "schedule"
#             ).order_by("-created_at")

#             connections_data = []

#             for conn in connections_qs:

#                 other_user = conn.receiver if conn.sender == user else conn.sender

#                 connections_data.append({
#                     "connection_request_id": conn.id,
#                     "connected_user": {
#                         "id": other_user.id,
#                         "name": getattr(other_user, "name", ""),
#                         "email": other_user.email,
#                         "role": getattr(other_user, "role", ""),
#                     },
#                     "profile": self.get_profile_data(other_user, request),
#                     "connected_at": conn.created_at,
#                     "connected_since": self.get_connected_since(conn.created_at),
#                     "upcoming_job": self.get_upcoming_job(conn),
#                 })

#             count = connections_qs.count()

#             return Response({
#                 "count": count,
#                 "connections": connections_data,
#                 "connection_limits": self.get_connection_limits(user, count),
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({
#                 "error": "Failed to fetch connections",
#                 "detail": str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
from profiles.models import LandscaperProfilies, ClientProfile
from reviews.models import LandscaperReview
from subscriptions.models import Subscription


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
    # RATING
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
    # PROFILE (USING SERIALIZERS - FIXED)
    # -----------------------------
    def get_profile_data(self, user, request):

        # ---------------- LANDSCAPER ----------------
        if hasattr(user, "landscaperprofilies"):
            profile = user.landscaperprofilies

            data = LandscaperProfileSerializer(
                profile,
                context={"request": request}
            ).data

            data.update({
                "type": "landscaper",
                "profile_image": profile.image.url if profile.image else None,
                "rating": self.get_rating(user),
            })

            return data

        # ---------------- CLIENT ----------------
        if hasattr(user, "clientprofile"):
            profile = user.clientprofile

            data = ClientProfileSerializer(
                profile,
                context={"request": request}
            ).data

            data.update({
                "type": "client",
                "profile_image": profile.image.url if profile.image else None,
                "rating": self.get_rating(user),
            })

            return data

        # ---------------- FALLBACK ----------------
        return {
            "user_id": user.id,
            "name": getattr(user, "name", ""),
            "email": user.email,
            "type": "unknown",
            "profile_image": None,
            "rating": self.get_rating(user),
        }

    # -----------------------------
    # CONNECTION LIMITS
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
    # MAIN API
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
                "upcoming_job": None,  # keep same structure
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

