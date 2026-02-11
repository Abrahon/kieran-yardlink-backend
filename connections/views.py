
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from services.models import ServiceSchedule ,ClientService
from rest_framework.exceptions import ValidationError
from accounts.models import User
from .models import ConnectionRequest
from .serializers import (
    ConnectionRequestDetailSerializer,
    SendConnectionRequestSerializer,
    RespondConnectionRequestSerializer,
    AcceptedConnectionSerializer,
)
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from profiles.models import ClientProfile, LandscaperProfilies
from landscapers.models import WorkingHours,Service
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from services.models import ServiceSchedule, ScheduleCompletionImage
from common.permissions import IsLandscaper
from django.db.models import Q
from profiles.serializers import ConnectedUserSerializer
from django.utils import timezone  # <-- ADD THIS
User = get_user_model()



class SendConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendConnectionRequestSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        receiver = User.objects.get(
            id=serializer.validated_data["receiver_id"]
        )

        connection = ConnectionRequest.objects.create(
            sender=request.user,
            receiver=receiver
        )

        return Response(
            ConnectionRequestDetailSerializer(
                connection,
                context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )


# class ConnectionRequestSerializer(serializers.ModelSerializer):
#     receiver_id = serializers.IntegerField(write_only=True)

#     class Meta:
#         model = ConnectionRequest
#         fields = ["id", "receiver_id", "is_accepted", "created_at"]

#     def validate_receiver_id(self, value):
#         try:
#             receiver = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("User not found.")

#         request_user = self.context["request"].user

#         if receiver == request_user:
#             raise serializers.ValidationError("You cannot send request to yourself.")

#         return receiver

#     def create(self, validated_data):
#         receiver = validated_data.pop("receiver_id")
#         sender = self.context["request"].user

#         return ConnectionRequest.objects.create(
#             sender=sender,
#             receiver=receiver
#         )


# inbox/views.py
class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1️⃣ Fetch all pending requests where the logged-in user is the receiver
        pending_requests = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted__isnull=True
        ).order_by("-created_at")

        response = []

        for req in pending_requests:
            sender = req.sender
            sender_data = {"user_id": sender.id, "email": sender.email, "type": "unknown"}

            #  Check if sender is landscaper
            try:
                sender_profile = sender.landscaperprofilies
                sender_data = LandscaperProfileSerializer(sender_profile, context={"request": request}).data
                sender_data["type"] = "landscaper"
            except LandscaperProfilies.DoesNotExist:
                #  Check if sender is client
                try:
                    sender_profile = sender.clientprofile
                    sender_data = ClientProfileSerializer(sender_profile, context={"request": request}).data
                    sender_data["type"] = "client"
                except ClientProfile.DoesNotExist:
                    pass  # keep as "unknown"

            #  Append to response
            response.append({
                "connection_id": req.id,
                "sent_by": sender_data,  # full profile of sender
                "created_at": req.created_at,
                "status": "pending"
            })

        return Response(response)



class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        return Response(ConnectionRequestDetailSerializer(qs, many=True).data)



# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request, pk):
#         user = request.user

#         # Fetch pending request
#         connection = get_object_or_404(
#             ConnectionRequest,
#             id=pk,
#             is_accepted=None
#         )

#         if user not in (connection.sender, connection.receiver):
#             return Response({"detail": "You are not part of this request."}, status=status.HTTP_403_FORBIDDEN)

#         # Identify roles
#         if hasattr(user, "clientprofile"):
#             responder_role = "client"
#             client_profile = user.clientprofile
#             landscaper_user = connection.receiver if connection.sender == user else connection.sender
#             landscaper_profile = get_object_or_404(LandscaperProfilies, user=landscaper_user)

#         elif hasattr(user, "landscaperprofilies"):
#             responder_role = "landscaper"
#             landscaper_profile = user.landscaperprofilies
#             client_user = connection.receiver if connection.sender == user else connection.sender
#             client_profile = get_object_or_404(ClientProfile, user=client_user)

#         else:
#             return Response({"detail": "Invalid user role."}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate action
#         serializer = RespondConnectionRequestSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         action = serializer.validated_data["action"]

#         # Reject
#         if action == "reject":
#             connection.is_accepted = False
#             connection.save(update_fields=["is_accepted"])
#             return Response({
#                 "connection_id": connection.id,
#                 "status": "rejected",
#                 "responded_by": responder_role
#             })

#         # Accept
#         connection.is_accepted = True
#         connection.save(update_fields=["is_accepted"])

#         # Client can only have one accepted landscaper
#         if responder_role == "client":
#             ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=user) | Q(receiver=user)
#             ).exclude(id=connection.id).delete()

#         # Create or fetch upcoming job for this client-landscaper
#         job = ServiceSchedule.objects.filter(
#             client=client_profile,
#             landscaper=landscaper_profile,
#             is_completed=False
#         ).first()

#         if not job:
#             now = timezone.now()
#             service = ClientService.objects.filter(landscaper=landscaper_profile).first()
#             if not service:
#                 return Response({"detail": "No client service found for this landscaper."}, status=status.HTTP_400_BAD_REQUEST)

#             job = ServiceSchedule.objects.create(
#                 client=client_profile,
#                 landscaper=landscaper_profile,
#                 service=service,
#                 scheduled_date=now.date(),
#                 scheduled_time=now.time()
#             )

#         # Attach schedule to connection
#         connection.schedule = job
#         connection.save(update_fields=["schedule"])

#         # Serialize client profile
#         client_data = ClientProfileSerializer(client_profile, context={"request": request}).data

#         return Response({
#             "connection_id": connection.id,
#             "status": "accepted",
#             "accepted_by": responder_role,
#             "upcoming_job": {
#                 "job_id": job.id,
#                 "date": job.scheduled_date,
#                 "time": job.scheduled_time
#             },
#             "client_profile": client_data
#         })


# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request, pk):
#         user = request.user


#         # Fetch pending request

#         connection = get_object_or_404(
#             ConnectionRequest,
#             id=pk,
#             is_accepted=None
#         )

#         if user not in (connection.sender, connection.receiver):
#             return Response(
#                 {"detail": "You are not part of this request."},
#                 status=status.HTTP_403_FORBIDDEN
#             )


#         # Identify roles

#         if hasattr(user, "clientprofile"):
#             responder_role = "client"
#             client_profile = user.clientprofile
#             landscaper_user = (
#                 connection.receiver if connection.sender == user else connection.sender
#             )
#             landscaper_profile = get_object_or_404(
#                 LandscaperProfilies,
#                 user=landscaper_user
#             )

#         elif hasattr(user, "landscaperprofilies"):
#             responder_role = "landscaper"
#             landscaper_profile = user.landscaperprofilies
#             client_user = (
#                 connection.receiver if connection.sender == user else connection.sender
#             )
#             client_profile = get_object_or_404(
#                 ClientProfile,
#                 user=client_user
#             )

#         else:
#             return Response(
#                 {"detail": "Invalid user role."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Validate action

#         serializer = RespondConnectionRequestSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         action = serializer.validated_data["action"]


#         # Reject request

#         if action == "reject":
#             connection.is_accepted = False
#             connection.save(update_fields=["is_accepted"])
#             return Response(
#                 {
#                     "connection_id": connection.id,
#                     "status": "rejected",
#                     "responded_by": responder_role
#                 }
#             )

#         # --------------------------------------------------
#         # Accept request
#         # --------------------------------------------------
#         connection.is_accepted = True
#         connection.save(update_fields=["is_accepted"])

#         # Count accepted connections for landscaper

#         accepted_connections_count = ConnectionRequest.objects.filter(
#             is_accepted=True
#         ).filter(
#             Q(sender=landscaper_profile.user) |
#             Q(receiver=landscaper_profile.user)
#         ).count()

#         # Enforce BASIC plan limit

#         if (
#             landscaper_profile.plan == LandscaperProfilies.BASIC
#             and accepted_connections_count > 10
#         ):
#             connection.is_accepted = None
#             connection.save(update_fields=["is_accepted"])

#             return Response(
#                 {
#                     "detail": (
#                         "Basic landscapers can connect with up to 10 clients only. "
#                         "Upgrade to PRO for unlimited connections."
#                     )
#                 },
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Client can have ONLY ONE landscaper

#         if responder_role == "client":
#             ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=user) | Q(receiver=user)
#             ).exclude(id=connection.id).delete()


#         # Create or fetch upcoming job

#         job = ServiceSchedule.objects.filter(
#             client=client_profile,
#             landscaper=landscaper_profile,
#             is_completed=False
#         ).first()

#         if not job:
#             now = timezone.now()
#             service = ClientService.objects.filter(
#                 landscaper=landscaper_profile
#             ).first()

#             if not service:
#                 return Response(
#                     {"detail": "No client service found for this landscaper."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             job = ServiceSchedule.objects.create(
#                 client=client_profile,
#                 landscaper=landscaper_profile,
#                 service=service,
#                 scheduled_date=now.date(),
#                 scheduled_time=now.time()
#             )

#         connection.schedule = job
#         connection.save(update_fields=["schedule"])

#         # Connection slot info (RESPONSE ONLY)

#         remaining_slots = None
#         connection_warning = None

#         if landscaper_profile.plan == LandscaperProfilies.BASIC:
#             MAX_CONNECTIONS = 10
#             remaining_slots = MAX_CONNECTIONS - accepted_connections_count

#             if accepted_connections_count == 8:
#                 connection_warning = (
#                     "You have used 8 out of 10 client connections. "
#                     "Consider upgrading to PRO for unlimited connections."
#                 )
#             elif accepted_connections_count == 9:
#                 connection_warning = (
#                     "You have only 1 client connection remaining. "
#                     "Upgrade to PRO to avoid connection limits."
#                 )

#         # Serialize client profile

#         client_data = ClientProfileSerializer(
#             client_profile,
#             context={"request": request}
#         ).data

#         return Response(
#             {
#                 "connection_id": connection.id,
#                 "status": "accepted",
#                 "accepted_by": responder_role,
#                 "upcoming_job": {
#                     "job_id": job.id,
#                     "date": job.scheduled_date,
#                     "time": job.scheduled_time
#                 },
#                 "client_profile": client_data,
#                 "connection_limits": {
#                     "plan": landscaper_profile.plan,
#                     "accepted_connections": accepted_connections_count,
#                     "remaining_slots": remaining_slots,
#                     "warning": connection_warning
#                 }
#             },
#             status=status.HTTP_200_OK
#         )
from django.utils import timezone  # ✅ Make sure timezone is imported



class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_landscaper_plan(self, landscaper_profile):
        """
        Helper method: return 'basic', 'pro', or 'free' based on active subscription.
        """
        subscription = (
            Subscription.objects
            .filter(
                user=landscaper_profile.user,
                is_active=True,
                tatus="active"
            )
            .select_related("plan")
            .first()
        )
        if subscription and subscription.plan:
            return subscription.plan.name.lower()  # e.g., "basic", "pro"
        return "free"

    @transaction.atomic
    def post(self, request, pk):
        user = request.user

        # Fetch pending connection request
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            is_accepted=None
        )

        if user not in (connection.sender, connection.receiver):
            return Response(
                {"detail": "You are not part of this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Identify roles
        if hasattr(user, "clientprofile"):
            responder_role = "client"
            client_profile = user.clientprofile
            landscaper_user = connection.receiver if connection.sender == user else connection.sender
            landscaper_profile = get_object_or_404(LandscaperProfilies, user=landscaper_user)

        elif hasattr(user, "landscaperprofilies"):
            responder_role = "landscaper"
            landscaper_profile = user.landscaperprofilies
            client_user = connection.receiver if connection.sender == user else connection.sender
            client_profile = get_object_or_404(ClientProfile, user=client_user)

        else:
            return Response({"detail": "Invalid user role."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate action
        serializer = RespondConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        # Reject request
        if action == "reject":
            connection.is_accepted = False
            connection.save(update_fields=["is_accepted"])
            return Response({
                "connection_id": connection.id,
                "status": "rejected",
                "responded_by": responder_role
            })

        # --------------------------------------------------
        # Accept request
        # --------------------------------------------------
        connection.is_accepted = True
        connection.save(update_fields=["is_accepted"])

        # Count accepted connections for landscaper
        accepted_connections_count = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=landscaper_profile.user) |
            Q(receiver=landscaper_profile.user)
        ).count()

        # ✅ Get plan dynamically from subscription
        plan = self.get_landscaper_plan(landscaper_profile)

        # Enforce BASIC plan limit
        if plan == "basic" and accepted_connections_count > 10:  # ✅ replace landscaper_profile.plan
            connection.is_accepted = None
            connection.save(update_fields=["is_accepted"])
            return Response({
                "detail": (
                    "Basic landscapers can connect with up to 10 clients only. "
                    "Upgrade to PRO for unlimited connections."
                )
            }, status=status.HTTP_403_FORBIDDEN)

        # Client can have ONLY ONE landscaper
        if responder_role == "client":
            ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=user) | Q(receiver=user)
            ).exclude(id=connection.id).delete()

        # Create or fetch upcoming job
        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).first()

        if not job:
            now = timezone.now()  # ✅ make sure timezone is imported
            service = ClientService.objects.filter(landscaper=landscaper_profile).first()

            if not service:
                return Response(
                    {"detail": "No client service found for this landscaper."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            job = ServiceSchedule.objects.create(
                client=client_profile,
                landscaper=landscaper_profile,
                service=service,
                scheduled_date=now.date(),
                scheduled_time=now.time()
            )

        connection.schedule = job
        connection.save(update_fields=["schedule"])

        # Connection slot info (RESPONSE ONLY)
        remaining_slots = None
        connection_warning = None

        if plan == "basic":  # ✅ replace landscaper_profile.plan
            MAX_CONNECTIONS = 10
            remaining_slots = MAX_CONNECTIONS - accepted_connections_count

            if accepted_connections_count == 8:
                connection_warning = (
                    "You have used 8 out of 10 client connections. "
                    "Consider upgrading to PRO for unlimited connections."
                )
            elif accepted_connections_count == 9:
                connection_warning = (
                    "You have only 1 client connection remaining. "
                    "Upgrade to PRO to avoid connection limits."
                )

        # Serialize client profile
        client_data = ClientProfileSerializer(client_profile, context={"request": request}).data

        return Response({
            "connection_id": connection.id,
            "status": "accepted",
            "accepted_by": responder_role,
            "upcoming_job": {
                "job_id": job.id,
                "date": job.scheduled_date,
                "time": job.scheduled_time
            },
            "client_profile": client_data,
            "connection_limits": {
                "plan": plan,  # ✅ return the plan here too
                "accepted_connections": accepted_connections_count,
                "remaining_slots": remaining_slots,
                "warning": connection_warning
            }
        }, status=status.HTTP_200_OK)


class CancelConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Fetch the connection where user is either sender or receiver
            connection = ConnectionRequest.objects.get(
                id=pk,
                is_accepted__isnull=True,
            )
            if request.user != connection.sender:
                # Only the sender can cancel pending requests
                return Response(
                    {"error": "Only sender can cancel this request"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ConnectionRequest.DoesNotExist:
            return Response(
                {"error": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        connection.delete()
        return Response(
            {"message": "Request cancelled"},
            status=status.HTTP_200_OK
        )





# Accepted Connections / Auto Schedule
# -------------------------------
# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         connections = ConnectionRequest.objects.filter(
#             Q(sender=request.user) | Q(receiver=request.user),
#             is_accepted=True
#         ).order_by("-created_at")

#         response_data = []
#         for conn in connections:
#             connected_user = conn.receiver if conn.sender == request.user else conn.sender
#             # Get profile
#             profile_data = self.get_profile_data(connected_user)
#             # Get upcoming job
#             upcoming_job = self.get_upcoming_job(request.user, connected_user)
#             response_data.append({
#                 "connection_id": conn.id,
#                 "connected_profile": profile_data,
#                 "created_at": conn.created_at,
#                 "upcoming_job": upcoming_job
#             })

#         serializer = ConnectedUserSerializer(response_data, many=True)
#         return Response(serializer.data)

#     def get_profile_data(self, user):
#         try:
#             profile = LandscaperProfilies.objects.get(user=user)
#             data = LandscaperProfileSerializer(profile).data
#             data["type"] = "landscaper"
#             return data
#         except LandscaperProfilies.DoesNotExist:
#             try:
#                 profile = ClientProfile.objects.get(user=user)
#                 data = ClientProfileSerializer(profile).data
#                 data["type"] = "client"
#                 return data
#             except ClientProfile.DoesNotExist:
#                 return {"user_id": user.id, "email": user.email, "name": getattr(user, "name", ""), "type": "unknown"}

#     def get_upcoming_job(self, current_user, other_user):
#         """
#         Fetch upcoming job between current_user and other_user,
#         regardless of who is landscaper/client
#         """
#         # Determine who is landscaper and who is client
#         landscaper_profile = getattr(current_user, "landscaper_profile", None) or getattr(other_user, "landscaper_profile", None)
#         client_profile = getattr(current_user, "clientprofile", None) or getattr(other_user, "clientprofile", None)

#         if not landscaper_profile or not client_profile:
#             return None

#         # Fetch next scheduled job
#         next_job = ServiceSchedule.objects.filter(
#             client=client_profile,
#             landscaper=landscaper_profile,
#             is_completed=False
#         ).order_by("scheduled_date", "scheduled_time").first()

#         if not next_job:
#             return None

#         return {
#             "service_name": next_job.service.name,
#             "date": next_job.scheduled_date,
#             "time": next_job.scheduled_time,
#             "price": next_job.service.price
#         }
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.models import Subscription  # your subscriptions app

class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get all accepted connections
        connections = ConnectionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_accepted=True
        ).select_related("sender", "receiver", "schedule").order_by("-created_at")

        response_data = []

        for conn in connections:
            other_user = conn.receiver if conn.sender == user else conn.sender

            # Try to fetch profiles
            landscaper_profile = LandscaperProfilies.objects.filter(user=other_user).first()
            client_profile = ClientProfile.objects.filter(user=other_user).first()

            if landscaper_profile:
                role = "landscaper"
                profile_data = LandscaperProfileSerializer(landscaper_profile).data
            elif client_profile:
                role = "client"
                profile_data = ClientProfileSerializer(client_profile).data
            else:
                continue

            # Upcoming job
            upcoming_job = None
            if conn.schedule:
                upcoming_job = {
                    "job_id": conn.schedule.id,
                    "service_name": conn.schedule.service.name,
                    "date": conn.schedule.scheduled_date,
                    "time": conn.schedule.scheduled_time,
                    "price": conn.schedule.service.price,
                    "payment_status": conn.schedule.payment_status,
                }

            response_data.append({
                "connection_id": conn.id,
                "connected_user": {
                    "id": other_user.id,
                    "name": getattr(other_user, "name", ""),
                    "email": other_user.email,
                    "role": role,
                },
                "profile": profile_data,
                "connected_at": conn.created_at,
                "upcoming_job": upcoming_job
            })

        # --------------------------------------------------
        # Connection limits for landscapers (BASIC/PRO)
        # --------------------------------------------------
        connection_limits = None
        landscaper_profile_self = LandscaperProfilies.objects.filter(user=user).first()

        if landscaper_profile_self:
            # Fetch subscription / plan
            subscription = Subscription.objects.filter(user=user, is_active=True).first()
            plan_name = subscription.plan if subscription else "BASIC"  # default BASIC if missing

            accepted_count = ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=user) | Q(receiver=user)
            ).count()

            if plan_name == "BASIC":
                connection_limits = {
                    "plan": "BASIC",
                    "accepted_connections": accepted_count,
                    "max_connections": 10,
                    "remaining_slots": max(0, 10 - accepted_count)
                }
            else:  # PRO
                connection_limits = {
                    "plan": "PRO",
                    "accepted_connections": accepted_count,
                    "max_connections": None,
                    "remaining_slots": None
                }

        return Response({
            "count": len(response_data),
            "connections": response_data,
            "connection_limits": connection_limits
        })



# -------------------------------
# Upcoming Job
# -------------------------------

from common.permissions import IsLandscaper
class UpcomingJobListAPIView(APIView):
    """
    Returns all pending jobs for the logged-in landscaper.
    Shows client profile for each job.
    """
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get(self, request):
        # 1️⃣ Get logged-in landscaper profile
        try:
            landscaper = request.user.landscaperprofilies
        except LandscaperProfilies.DoesNotExist:
            return Response([])

        # 2️⃣ Fetch all pending jobs assigned to this landscaper
        jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper,
            is_completed=False
        ).select_related("client", "service").order_by("scheduled_date", "scheduled_time")

        response = []

        for job in jobs:
            client_profile = job.client

            # 3️⃣ Ensure the job is linked to an accepted connection
            connection_exists = ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=client_profile.user, receiver=request.user) |
                Q(sender=request.user, receiver=client_profile.user)
            ).exists()

            if not connection_exists:
                continue  # skip jobs without accepted connection

            # 4️⃣ Append job info
            response.append({
                "job_id": job.id,
                "service_name": job.service.name,
                "scheduled_date": job.scheduled_date,
                "scheduled_time": job.scheduled_time,
                "price": float(job.service.price or 0),
                "client": ClientProfileSerializer(client_profile, context={"request": request}).data
            })

        return Response(response)

class RemoveConnectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            is_accepted=True
        )

        if request.user not in [connection.sender, connection.receiver]:
            return Response(
                {"detail": "Permission denied"},
                status=403
            )

        connection.delete()
        return Response(
            {"message": "Connection removed"}
        )


# class JobDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsLandscaper]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]

#     def patch(self, request, job_id):
#         job = get_object_or_404(ServiceSchedule, id=job_id)

#         #  Only assigned landscaper can update
#         landscaper = request.user.landscaperprofilies
#         if job.landscaper != landscaper:
#             return Response(
#                 {"detail": "You are not assigned to this job"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         #  Update schedule fields
#         if "scheduled_date" in request.data:
#             job.scheduled_date = request.data["scheduled_date"]

#         if "scheduled_time" in request.data:
#             job.scheduled_time = request.data["scheduled_time"]

#         #  Mark job as completed
#         if request.data.get("is_completed") in [True, "true", "True"]:
#             if not job.is_completed:
#                 job.is_completed = True
#                 job.completed_at = timezone.now()

#         # Save ONE completion note (job-level)
#         if "completion_note" in request.data:
#             job.completion_note = request.data["completion_note"]

#         job.save()

#         #  Upload images ONLY after completion
#         images = request.FILES.getlist("images")

#         if images:
#             if not job.is_completed:
#                 return Response(
#                     {"error": "Complete the job before uploading images"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             for image in images:
#                 ScheduleCompletionImage.objects.create(
#                     schedule=job,
#                     image=image
#                 )

#         # Serialize images
#         image_urls = [img.image.url for img in job.images.all()]

#         return Response({
#             "job_id": job.id,
#             "service": job.service.name,
#             "scheduled_date": job.scheduled_date,
#             "scheduled_time": job.scheduled_time,
#             "is_completed": job.is_completed,
#             "completed_at": job.completed_at,
#             "completion_note": job.completion_note,  
#             "payment_status": "pending" if job.is_completed else None,
#             "images": image_urls,
#             "client": ClientProfileSerializer(
#                 job.client,
#                 context={"request": request}
#             ).data
#         })



class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLandscaper]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, job_id):
        """
        GET job details by job_id
        """
        job = get_object_or_404(ServiceSchedule, id=job_id)
        return Response({
            "job_id": job.id,
            "service": job.service.name,
            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,
            "is_completed": job.is_completed,
            "completed_at": job.completed_at,
            "completion_note": job.completion_note,
            "payment_status": job.payment_status,
            "images": [img.image.url for img in job.images.all()],
            "client": ClientProfileSerializer(job.client, context={"request": request}).data
        }, status=status.HTTP_200_OK)

    def patch(self, request, job_id):
        """
        PATCH to update job details (scheduled date/time, completion, note) 
        and upload images after completion.
        """
        job = get_object_or_404(ServiceSchedule, id=job_id)

        # Only assigned landscaper can update
        landscaper = getattr(request.user, "landscaperprofilies", None)
        if not landscaper or job.landscaper != landscaper:
            return Response(
                {"detail": "You are not assigned to this job"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update schedule fields
        if "scheduled_date" in request.data:
            job.scheduled_date = request.data["scheduled_date"]

        if "scheduled_time" in request.data:
            job.scheduled_time = request.data["scheduled_time"]

        # Mark job as completed
        if request.data.get("is_completed") in [True, "true", "True"]:
            if not job.is_completed:
                job.is_completed = True
                job.completed_at = timezone.now()

        # Save completion note
        if "completion_note" in request.data:
            job.completion_note = request.data["completion_note"]

        job.save()

        # Handle image uploads after completion
        images = request.FILES.getlist("images")
        if images:
            if not job.is_completed:
                return Response(
                    {"error": "Complete the job before uploading images"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            for img in images:
                ScheduleCompletionImage.objects.create(schedule=job, image=img)

        # Serialize images
        image_urls = [img.image.url for img in job.images.all()]

        return Response({
            "job_id": job.id,
            "service": job.service.name,
            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,
            "is_completed": job.is_completed,
            "completed_at": job.completed_at,
            "completion_note": job.completion_note,
            "payment_status": job.payment_status,
            "images": image_urls,
            "client": ClientProfileSerializer(job.client, context={"request": request}).data
        }, status=status.HTTP_200_OK)
