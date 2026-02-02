from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from services.models import ServiceSchedule ,Service
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
from .models import ConnectionRequest
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from services.models import ServiceSchedule
from profiles.models import ClientProfile, LandscaperProfilies
from accounts.models import User

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from connections.models import ConnectionRequest
from landscapers.models import WorkingHours
from services.models import Service, ServiceSchedule
from profiles.models import ClientProfile
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

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


class ConnectionRequestSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ["id", "receiver_id", "is_accepted", "created_at"]

    def validate_receiver_id(self, value):
        try:
            receiver = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        request_user = self.context["request"].user

        if receiver == request_user:
            raise serializers.ValidationError("You cannot send request to yourself.")

        return receiver

    def create(self, validated_data):
        receiver = validated_data.pop("receiver_id")
        sender = self.context["request"].user

        return ConnectionRequest.objects.create(
            sender=sender,
            receiver=receiver
        )


# inbox/views.py
class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted__isnull=True  # Only pending
        ).order_by("-created_at")

        print("Queryset:", qs)  # Debug: check what it returns
        serializer = ConnectionRequestDetailSerializer(qs, many=True, context={"request": request})
        print("Serialized data:", serializer.data)  # Debug: check serialized output
        return Response(serializer.data)


class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        return Response(ConnectionRequestSerializer(qs, many=True).data)




# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         connection = get_object_or_404(
#             ConnectionRequest,
#             id=pk,
#             receiver=request.user,
#             is_accepted=None
#         )

#         serializer = RespondConnectionRequestSerializer(
#             instance=connection,
#             data=request.data
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(ConnectionRequestSerializer(connection).data)

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db.models import Q
# from connections.models import ConnectionRequest
# from profiles.models import LandscaperProfilies, ClientProfile
# # from .serializers import ConnectedUserSerializer, RespondConnectionRequestSerializer
# from services.models import ServiceSchedule


# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         # 1️⃣ Get the pending connection request
#         try:
#             connection = ConnectionRequest.objects.get(
#                 id=pk,
#                 receiver=request.user,
#                 is_accepted=None
#             )
#         except ConnectionRequest.DoesNotExist:
#             return Response(
#                 {"detail": "Connection request not found or already responded."},
#                 status=404
#             )

#         # 2️⃣ Update connection request (accept/reject)
#         serializer = RespondConnectionRequestSerializer(
#             instance=connection,
#             data=request.data
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         # 3️⃣ Get the connected user (other side)
#         connected_user = connection.receiver if connection.sender == request.user else connection.sender

#         # 4️⃣ Get profile data
#         profile_data = self.get_profile_data(connected_user)

#         # 5️⃣ Get all upcoming jobs if connection was accepted
#         upcoming_jobs = []
#         if connection.is_accepted:
#             upcoming_jobs = self.get_upcoming_jobs(request.user, connected_user)

#         # 6️⃣ Build response
#         response_data = {
#             "connection_id": connection.id,
#             "connected_profile": profile_data,
#             "created_at": connection.created_at,
#             "upcoming_jobs": upcoming_jobs  # changed from single "upcoming_job"
#         }

#         serializer = ConnectedUserSerializer(response_data)
#         return Response(serializer.data)

#     # ----------------------
#     def get_profile_data(self, user):
#         try:
#             profile = LandscaperProfilies.objects.get(user=user)
#             data = ConnectedUserSerializer(profile).data
#             data["type"] = "landscaper"
#             return data
#         except LandscaperProfilies.DoesNotExist:
#             try:
#                 profile = ClientProfile.objects.get(user=user)
#                 data = ConnectedUserSerializer(profile).data
#                 data["type"] = "client"
#                 return data
#             except ClientProfile.DoesNotExist:
#                 return {
#                     "user_id": user.id,
#                     "email": user.email,
#                     "name": getattr(user, "name", ""),
#                     "type": "unknown"
#                 }
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from connections.models import ConnectionRequest
from connections.serializers import RespondConnectionRequestSerializer
from profiles.models import ClientProfile, LandscaperProfilies
from services.models import ServiceSchedule


class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user

        # 🔒 Only CLIENT can respond
        try:
            client_profile = user.clientprofile
        except ClientProfile.DoesNotExist:
            raise PermissionDenied("Only clients can respond to connection requests.")

        # 🔍 Fetch pending request
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            is_accepted=None
        )

        if user not in (connection.sender, connection.receiver):
            raise PermissionDenied("You are not part of this request.")

        # 🌿 Identify landscaper PROFILE (SAFE)
        if hasattr(connection.sender, "landscaperprofilies"):
            landscaper_profile = connection.sender.landscaperprofilies
        elif hasattr(connection.receiver, "landscaperprofilies"):
            landscaper_profile = connection.receiver.landscaperprofilies
        else:
            raise PermissionDenied("No landscaper found in this connection.")

        serializer = RespondConnectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        # ❌ REJECT
        if action == "reject":
            connection.is_accepted = False
            connection.save(update_fields=["is_accepted"])
            return Response({
                "connection_id": connection.id,
                "status": "rejected"
            })

        # ✅ ACCEPT
        connection.is_accepted = True
        connection.save(update_fields=["is_accepted"])

        # 🔥 ENFORCE: CLIENT → ONLY ONE LANDSCAPER
        ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=user) | Q(receiver=user)
        ).exclude(
            id=connection.id
        ).delete()

        # 📅 UPCOMING JOB (CLIENT ONLY)
        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).order_by(
            "scheduled_date", "scheduled_time"
        ).first()

        # 🆕 Create job if not exists
        if not job:
            now = timezone.now()
            job = ServiceSchedule.objects.create(
                client=client_profile,
                landscaper=landscaper_profile,
                scheduled_date=now.date(),
                scheduled_time=now.time(),
            )

        # 🔗 Attach schedule
        connection.schedule = job
        connection.save(update_fields=["schedule"])

        return Response({
            "connection_id": connection.id,
            "status": "accepted",
            "client_id": client_profile.id,
            "landscaper_id": landscaper_profile.id,
            "upcoming_job": {
                "job_id": job.id,
                "date": job.scheduled_date,
                "time": job.scheduled_time,
            }
        })

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



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from connections.models import ConnectionRequest
from profiles.models import LandscaperProfilies, ClientProfile
from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
from profiles.serializers import ConnectedUserSerializer


# Accepted Connections / Auto Schedule
# -------------------------------
class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connections = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            is_accepted=True
        ).order_by("-created_at")

        response_data = []
        for conn in connections:
            connected_user = conn.receiver if conn.sender == request.user else conn.sender
            # Get profile
            profile_data = self.get_profile_data(connected_user)
            # Get upcoming job
            upcoming_job = self.get_upcoming_job(request.user, connected_user)
            response_data.append({
                "connection_id": conn.id,
                "connected_profile": profile_data,
                "created_at": conn.created_at,
                "upcoming_job": upcoming_job
            })

        serializer = ConnectedUserSerializer(response_data, many=True)
        return Response(serializer.data)

    def get_profile_data(self, user):
        try:
            profile = LandscaperProfilies.objects.get(user=user)
            data = LandscaperProfileSerializer(profile).data
            data["type"] = "landscaper"
            return data
        except LandscaperProfilies.DoesNotExist:
            try:
                profile = ClientProfile.objects.get(user=user)
                data = ClientProfileSerializer(profile).data
                data["type"] = "client"
                return data
            except ClientProfile.DoesNotExist:
                return {"user_id": user.id, "email": user.email, "name": getattr(user, "name", ""), "type": "unknown"}

    def get_upcoming_job(self, current_user, other_user):
        """
        Fetch upcoming job between current_user and other_user,
        regardless of who is landscaper/client
        """
        # Determine who is landscaper and who is client
        landscaper_profile = getattr(current_user, "landscaper_profile", None) or getattr(other_user, "landscaper_profile", None)
        client_profile = getattr(current_user, "clientprofile", None) or getattr(other_user, "clientprofile", None)

        if not landscaper_profile or not client_profile:
            return None

        # Fetch next scheduled job
        next_job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not next_job:
            return None

        return {
            "service_name": next_job.service.name,
            "date": next_job.scheduled_date,
            "time": next_job.scheduled_time,
            "price": next_job.service.price
        }



# -------------------------------
# Accept Connection and Auto-Schedule
# -------------------------------

# class AcceptConnectionAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, request_id):
#         conn = get_object_or_404(
#             ConnectionRequest,
#             id=request_id,
#             receiver=request.user,
#             is_accepted=None
#         )

#         conn.is_accepted = True
#         conn.save(update_fields=["is_accepted"])

#         # ✅ AUTO SCHEDULE
#         if not conn.schedule:
#             schedule = self.auto_schedule_client(conn)
#             conn.schedule = schedule
#             conn.save(update_fields=["schedule"])
#         else:
#             schedule = conn.schedule

#         client_profile = conn.sender.clientprofile

#         return Response({
#             "message": "Connection accepted and scheduled",
#             "scheduled_job": {
#                 "schedule_id": schedule.id,
#                 "service": schedule.service.name,
#                 "date": schedule.scheduled_date,
#                 "time": schedule.scheduled_time,
#                 "price": schedule.service.price
#             } if schedule else None
#         })

  
#     def auto_schedule_client(self, conn):
#         client = conn.sender.clientprofile
#         landscaper = conn.receiver.landscaper_profile

#         service = Service.objects.filter(
#             landscaper=landscaper,
#             is_standard=True
#         ).first()

#         if not service:
#             return None

#         today = datetime.today().date()

#         for i in range(7):
#             check_date = today + timedelta(days=i)
#             weekday = check_date.strftime("%A").upper()

#             working_hours = WorkingHours.objects.filter(
#                 landscaper=landscaper,
#                 day=weekday
#             ).first()

#             if working_hours:
#                 return ServiceSchedule.objects.create(
#                     client=client,
#                     landscaper=landscaper,
#                     service=service,
#                     scheduled_date=check_date,
#                     scheduled_time=working_hours.start_time
#                 )

#         return None
class AcceptConnectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connections = ConnectionRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            is_accepted=True
        ).order_by("-created_at")

        response_data = []

        for conn in connections:
            # 🔹 find the other user
            other_user = conn.receiver if conn.sender == request.user else conn.sender

            # 🔹 get upcoming job (THIS IS WHERE YOUR FUNCTION IS USED)
            upcoming_job = self.get_upcoming_job(request.user, other_user)

            if not upcoming_job:
                continue

            # 🔹 landscaper profile (for display)
            try:
                landscaper_profile = LandscaperProfilies.objects.get(user=other_user)
            except LandscaperProfilies.DoesNotExist:
                continue

            response_data.append({
                "connection_id": conn.id,
                "landscaper": LandscaperProfileSerializer(landscaper_profile).data,
                "upcoming_job": upcoming_job,
                "created_at": conn.created_at,
            })

        return Response(response_data)

    # 🔹 ADD YOUR METHOD HERE
    def get_upcoming_job(self, current_user, other_user):
        try:
            client_profile = current_user.clientprofile
        except ClientProfile.DoesNotExist:
            return None

        try:
            landscaper_profile = LandscaperProfilies.objects.get(user=other_user)
        except LandscaperProfilies.DoesNotExist:
            return None

        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not job:
            return None

        return {
            "job_id": job.id,
            "service_name": job.service.category or job.service.name,
            "date": job.scheduled_date,
            "time": job.scheduled_time,
            "price": float(job.service.price or 0),
        }

# -------------------------------
# Upcoming Job
# -------------------------------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from services.models import ServiceSchedule
from profiles.models import LandscaperProfilies
from connections.models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer


class UpcomingJobAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1️⃣ Ensure landscaper
        try:
            landscaper = request.user.landscaperprofilies
        except LandscaperProfilies.DoesNotExist:
            return Response([])

        # 2️⃣ Fetch upcoming jobs
        jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper,
            is_completed=False
        ).select_related(
            "client", "client__user", "service"
        ).order_by("scheduled_date", "scheduled_time")

        response = []

        for job in jobs:
            client_profile = job.client

            # 3️⃣ Ensure ACCEPTED connection
            is_connected = ConnectionRequest.objects.filter(
                is_accepted=True,
                sender__in=[request.user, client_profile.user],
                receiver__in=[request.user, client_profile.user]
            ).exists()

            if not is_connected:
                continue  # ⛔ skip non-connected clients

            response.append({
                "job_id": job.id,
                "scheduled_date": job.scheduled_date,
                "scheduled_time": job.scheduled_time,
                "service_name": job.service.name,
                "price": float(job.service.price or 0),

                # 🔥 FULL CLIENT PROFILE + PROPERTIES
                "client": ClientProfileWithPropertySerializer(client_profile).data
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
