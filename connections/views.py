
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now

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


class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        connection = get_object_or_404(ConnectionRequest, id=pk)

        if connection.is_accepted is not None:
            return Response(
                {"detail": "This connection request has already been responded to."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user not in (connection.sender, connection.receiver):
            return Response(
                {"detail": "You are not part of this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RespondConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        sender = connection.sender
        receiver = connection.receiver

        # -------------------------
        # Determine roles from user.role
        # -------------------------
        if sender.role == "client" and receiver.role == "landscaper":
            client_user = sender
            landscaper_user = receiver
        elif sender.role == "landscaper" and receiver.role == "client":
            client_user = receiver
            landscaper_user = sender
        else:
            return Response(
                {"detail": "Connection must be between one client and one landscaper."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------
        # Fetch required profiles
        # -------------------------
        client_profile = ClientProfile.objects.filter(user=client_user).first()
        landscaper_business = BusinessProfile.objects.filter(user=landscaper_user).first()
        landscaper_basic = LandscaperProfilies.objects.filter(user=landscaper_user).first()

        if not client_profile:
            return Response(
                {"detail": "Client profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not landscaper_business:
            return Response(
                {"detail": "Landscaper business profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not landscaper_basic:
            return Response(
                {"detail": "Landscaper basic profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------
        # Reject
        # -------------------------
        if action == "reject":
            connection.is_accepted = False
            connection.save(update_fields=["is_accepted"])

            return Response(
                {
                    "connection_id": connection.id,
                    "status": "rejected",
                    "responded_by": user.role,
                    "client_profile": ClientProfileSerializer(
                        client_profile,
                        context={"request": request}
                    ).data,
                    "landscaper_profile": LandscaperProfileSerializer(
                        landscaper_business,
                        context={"request": request}
                    ).data,
                },
                status=status.HTTP_200_OK
            )

        # -------------------------
        # Check landscaper plan limits
        # -------------------------
        accepted_connections_count = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=landscaper_user) | Q(receiver=landscaper_user)
        ).count()

        subscription = Subscription.objects.filter(
            user=landscaper_user,
            is_active=True,
            status=SubscriptionStatus.ACTIVE
        ).select_related("plan").order_by("-end_date").first()

        if subscription and subscription.plan:
            plan_name = subscription.plan.name.lower()
        elif landscaper_basic.plan:
            plan_name = landscaper_basic.plan.name.lower()
        else:
            plan_name = "free"

        if plan_name == "basic" and accepted_connections_count >= 10:
            return Response(
                {
                    "detail": "Basic landscapers can connect with up to 10 clients only. Upgrade to PRO for unlimited connections."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # -------------------------
        # Accept connection
        # -------------------------
        connection.is_accepted = True
        connection.save(update_fields=["is_accepted"])

        # one client -> one accepted landscaper
        if user.role == "client":
            ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=client_user) | Q(receiver=client_user)
            ).exclude(id=connection.id).delete()

        # -------------------------
        # Get landscaper service
        # -------------------------
        service_obj = Service.objects.filter(
            business=landscaper_business
        ).order_by("-created_at").first()

        if not service_obj:
            connection.is_accepted = None
            connection.save(update_fields=["is_accepted"])
            return Response(
                {"detail": "This landscaper has not created any services yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_service, created = ClientService.objects.get_or_create(
            landscaper=landscaper_basic,
            name=getattr(service_obj, "name", "Service"),
            defaults={
                "description": getattr(service_obj, "description", "") or "",
                "category": getattr(service_obj, "category", "general"),
                "price": getattr(service_obj, "price", 0) or 0,
                "square_feet": getattr(service_obj, "square_feet", 0) or 0,
                "is_standard": getattr(service_obj, "category", "") == "standard",
            }
        )

        # -------------------------
        # Create or fetch upcoming job
        # -------------------------
        job = Job.objects.filter(
            client=client_profile,
            landscaper=landscaper_basic,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not job:
            current_time = timezone.now()
            job = Job.objects.create(
                client=client_profile,
                landscaper=landscaper_basic,
                service=client_service,
                scheduled_date=current_time.date(),
                scheduled_time=current_time.time(),
            )

        connection.schedule = job
        connection.save(update_fields=["schedule"])

        # -------------------------
        # Connection limit info
        # -------------------------
        remaining_slots = None
        connection_warning = None

        if plan_name == "basic":
            max_connections = 10
            remaining_slots = max_connections - (accepted_connections_count + 1)

            if remaining_slots == 2:
                connection_warning = "You have used 8 out of 10 client connections. Consider upgrading to PRO."
            elif remaining_slots == 1:
                connection_warning = "You have only 1 client connection remaining. Upgrade to PRO to avoid limits."

        # -------------------------
        # Serialize both profiles
        # -------------------------
        client_data = ClientProfileSerializer(
            client_profile,
            context={"request": request}
        ).data

        landscaper_data = LandscaperProfileSerializer(
            landscaper_business,
            context={"request": request}
        ).data

        return Response(
            {
                "connection_id": connection.id,
                "status": "accepted",
                "accepted_by": user.role,
                "client_profile": client_data,
                "landscaper_profile": landscaper_data,
                "upcoming_job": {
                    "job_id": job.id,
                    "service_name": getattr(job.service, "name", "Service"),
                    "date": job.scheduled_date,
                    "time": job.scheduled_time,
                    "price": float(getattr(job.service, "price", 0) or 0),
                },
                "connection_limits": {
                    "plan": plan_name,
                    "accepted_connections": accepted_connections_count + 1,
                    "remaining_slots": remaining_slots,
                    "warning": connection_warning,
                },
            },
            status=status.HTTP_200_OK
        )

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

# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get_profile_data(self, user, request):
#         """
#         Return profile data based on user type.
#         """
#         business_profile = getattr(user, "landscaper_profile", None)
#         basic_profile = getattr(user, "landscaperprofilies", None)
#         client_profile = getattr(user, "client_profile", None)

#         if business_profile:
#             data = BusinessLandscaperProfileSerializer(
#                 business_profile,
#                 context={"request": request}
#             ).data
#             data["user_id"] = user.id
#             data["email"] = user.email
#             data["type"] = "landscaper_business"
#             return data

#         if basic_profile:
#             return {
#                 "user_id": user.id,
#                 "name": basic_profile.name,
#                 "phone": basic_profile.phone,
#                 "image": basic_profile.image.url if basic_profile.image else None,
#                 "type": "landscaper_basic",
#             }

#         if client_profile:
#             data = ClientProfileSerializer(
#                 client_profile,
#                 context={"request": request}
#             ).data
#             data["user_id"] = user.id
#             data["email"] = user.email
#             data["type"] = "client"
#             return data

#         return {
#             "user_id": user.id,
#             "name": getattr(user, "name", ""),
#             "email": user.email,
#             "type": "unknown",
#         }

#     def get_connected_since(self, created_at):
#         diff = timezone.now() - created_at

#         if diff.days > 0:
#             return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
#         elif diff.seconds >= 3600:
#             hours = diff.seconds // 3600
#             return f"{hours} hour{'s' if hours != 1 else ''} ago"
#         elif diff.seconds >= 60:
#             minutes = diff.seconds // 60
#             return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
#         return "just now"

#     def get_upcoming_job(self, conn):
#         if not conn.schedule:
#             return None

#         schedule = conn.schedule

#         return {
#             "job_id": schedule.id,
#             "service_name": getattr(schedule.service, "name", None) if schedule.service else None,
#             "date": schedule.scheduled_date,
#             "time": schedule.scheduled_time,
#             "price": float(getattr(schedule.service, "price", 0) or 0) if schedule.service else 0,
#             "payment_status": getattr(schedule, "payment_status", None),
#             "is_completed": schedule.is_completed,
#         }

#     def get(self, request):
#         user = request.user

#         connections = ConnectionRequest.objects.filter(
#             Q(sender=user) | Q(receiver=user),
#             is_accepted=True
#         ).select_related(
#             "sender",
#             "receiver",
#             "schedule",
#             "schedule__service"
#         ).order_by("-created_at")

#         response_data = []

#         for conn in connections:
#             connected_user = conn.receiver if conn.sender == user else conn.sender

#             response_data.append({
#                 "connection_request_id": conn.id,
#                 "connected_user": {
#                     "id": connected_user.id,
#                     "name": getattr(connected_user, "name", ""),
#                     "email": connected_user.email,
#                     "role": getattr(connected_user, "role", None),
#                 },
#                 "profile": self.get_profile_data(connected_user, request),
#                 "connected_at": conn.created_at,
#                 "connected_since": self.get_connected_since(conn.created_at),
#                 "upcoming_job": self.get_upcoming_job(conn),
#             })

#         return Response(
#             {
#                 "total_count": connections.count(),
#                 "connections": response_data,
#             },
#             status=status.HTTP_200_OK
#         )



class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_profile_data(self, user, request):
        business_profile = getattr(user, "landscaper_profile", None)
        basic_profile = getattr(user, "landscaperprofilies", None)
        client_profile = getattr(user, "client_profile", None)

        if business_profile:
            data = BusinessLandscaperProfileSerializer(
                business_profile,
                context={"request": request}
            ).data
            data["user_id"] = user.id
            data["email"] = user.email
            data["type"] = "landscaper_business"
            return data

        if basic_profile:
            return {
                "user_id": user.id,
                "name": getattr(basic_profile, "name", ""),
                "phone": getattr(basic_profile, "phone", ""),
                "image": basic_profile.image.url if getattr(basic_profile, "image", None) else None,
                "type": "landscaper_basic",
            }

        if client_profile:
            data = ClientProfileSerializer(
                client_profile,
                context={"request": request}
            ).data
            data["user_id"] = user.id
            data["email"] = user.email
            data["type"] = "client"
            return data

        return {
            "user_id": user.id,
            "name": getattr(user, "name", ""),
            "email": user.email,
            "type": "unknown",
        }

    def get_connected_since(self, created_at):
        diff = timezone.now() - created_at

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        if diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        return "just now"

    def get_upcoming_job(self, conn):
        if not conn.schedule:
            return None

        schedule = conn.schedule
        service = getattr(schedule, "service", None)

        return {
            "job_id": schedule.id,
            "service_name": getattr(service, "name", None),
            "date": schedule.scheduled_date,
            "time": schedule.scheduled_time,
            "price": float(getattr(service, "price", 0) or 0),
            "payment_status": getattr(schedule, "payment_status", None),
            "is_completed": getattr(schedule, "is_completed", False),
        }

    def get_connection_limits(self, user, accepted_count):
        landscaper_business = getattr(user, "landscaper_profile", None)
        landscaper_basic = getattr(user, "landscaperprofilies", None)

        if not landscaper_business and not landscaper_basic:
            return None

        subscription = Subscription.objects.filter(
            user=user,
            is_active=True,
            status=SubscriptionStatus.ACTIVE
        ).select_related("plan").order_by("-end_date").first()

        if subscription and subscription.plan:
            plan_name = subscription.plan.name.upper()
        elif landscaper_basic and getattr(landscaper_basic, "plan", None):
            plan_name = landscaper_basic.plan.name.upper()
        else:
            plan_name = "BASIC"

        if plan_name == "BASIC":
            max_connections = 10
            return {
                "plan": plan_name,
                "accepted_connections": accepted_count,
                "max_connections": max_connections,
                "remaining_slots": max(0, max_connections - accepted_count),
            }

        return {
            "plan": plan_name,
            "accepted_connections": accepted_count,
            "max_connections": None,
            "remaining_slots": None,
        }

    def get(self, request):
        user = request.user
        now = timezone.now()

        connections_qs = ConnectionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_accepted=True
        ).select_related(
            "sender",
            "receiver",
            "schedule",
            "schedule__service"
        ).order_by("-created_at")

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
                "upcoming_job": self.get_upcoming_job(conn),
            })

        count = connections_qs.count()

        first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_last_day = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_month_last_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        active_users_this_month_qs = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_this_month
        ).values_list("sender_id", "receiver_id")

        active_users_last_month_qs = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_last_month,
            created_at__lt=first_day_this_month
        ).values_list("sender_id", "receiver_id")

        active_this_month_users = {
            user_id
            for pair in active_users_this_month_qs
            for user_id in pair
            if user_id is not None
        }

        active_last_month_users = {
            user_id
            for pair in active_users_last_month_qs
            for user_id in pair
            if user_id is not None
        }

        total_active_system_users = User.objects.filter(is_active=True).count()

        active_percentage = (
            round((len(active_this_month_users) / total_active_system_users) * 100, 1)
            if total_active_system_users > 0 else 0.0
        )

        previous_month_percentage = (
            round((len(active_last_month_users) / total_active_system_users) * 100, 1)
            if total_active_system_users > 0 else 0.0
        )

        diff = round(active_percentage - previous_month_percentage, 1)
        if diff > 0:
            change_vs_last_month = f"+{diff}"
        elif diff < 0:
            change_vs_last_month = f"{diff}"
        else:
            change_vs_last_month = "0.0"

        connection_limits = self.get_connection_limits(user, count)

        return Response(
            {
                "count": count,
                "connections": connections_data,
                "active_percentage": active_percentage,
                "previous_month_percentage": previous_month_percentage,
                "change_vs_last_month": change_vs_last_month,
                "connection_limits": connection_limits,
            },
            status=status.HTTP_200_OK
        )

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


# class TodayJobsAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsLandscaper]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]

#     def get_job_response(self, job):
#         completed_services = job.completed_services.all()
#         total_price = sum(s.price for s in completed_services)

#         before_images = [img.image.url for img in job.images.filter(image_type="before")]
#         after_images = [img.image.url for img in job.images.filter(image_type="after")]

#         client_data = {
#             "id": job.client.id,
#             "name": getattr(job.client, "name", ""),
#             "email": job.client.user.email,
#             "phone": getattr(job.client, "phone", ""),
#             "address": getattr(job.client, "address", ""),
#             "profile_image": job.client.image.url if getattr(job.client, "image", None) else None,
#         }

#         return {
#             "job_id": job.id,
#             "service": getattr(job.service, "name", None),
#             "scheduled_date": job.scheduled_date,
#             "scheduled_time": job.scheduled_time,
#             "is_completed": job.is_completed,
#             "completed_at": job.completed_at,
#             "completion_note": job.completion_note,
#             "payment_status": job.payment_status,
#             "total_price": total_price,
#             "completed_services": [
#                 {"id": s.id, "name": s.name, "price": s.price}
#                 for s in completed_services
#             ],
#             "before_images": before_images,
#             "after_images": after_images,
#             "client": client_data,
#         }

#     def get(self, request):
#         landscaper = getattr(request.user, "landscaperprofilies", None)
#         if not landscaper:
#             return Response(
#                 {"detail": "You are not a landscaper"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         current_time = timezone.now()

#         todays_jobs = Job.objects.filter(
#             landscaper=landscaper,
#             scheduled_date__year=current_time.year,
#             scheduled_date__month=current_time.month,
#             scheduled_date__day=current_time.day
#         ).order_by("scheduled_time")

#         response_data = [self.get_job_response(job) for job in todays_jobs]

#         return Response(
#             {
#                 "count": len(response_data),
#                 "jobs": response_data,
#             },
#             status=status.HTTP_200_OK
#         )