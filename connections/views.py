
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
from .models import ConnectionRequest
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from profiles.models import ClientProfile, LandscaperProfilies
from landscapers.models import WorkingHours,Service
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
from django.db import transaction
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from services.models import ServiceSchedule, ScheduleCompletionImage
from common.permissions import IsLandscaper
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

        return Response(ConnectionRequestSerializer(qs, many=True).data)




class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user

        # Fetch pending request
        connection = get_object_or_404(
            ConnectionRequest,
            id=pk,
            is_accepted=None
        )

        if user not in (connection.sender, connection.receiver):
            return Response({"detail": "You are not part of this request."}, status=status.HTTP_403_FORBIDDEN)

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

        # Reject
        if action == "reject":
            connection.is_accepted = False
            connection.save(update_fields=["is_accepted"])
            return Response({
                "connection_id": connection.id,
                "status": "rejected",
                "responded_by": responder_role
            })

        # Accept
        connection.is_accepted = True
        connection.save(update_fields=["is_accepted"])

        # Client can only have one accepted landscaper
        if responder_role == "client":
            ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=user) | Q(receiver=user)
            ).exclude(id=connection.id).delete()

        # Create or fetch upcoming job for this client-landscaper
        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).first()

        if not job:
            now = timezone.now()
            service = ClientService.objects.filter(landscaper=landscaper_profile).first()
            if not service:
                return Response({"detail": "No client service found for this landscaper."}, status=status.HTTP_400_BAD_REQUEST)

            job = ServiceSchedule.objects.create(
                client=client_profile,
                landscaper=landscaper_profile,
                service=service,
                scheduled_date=now.date(),
                scheduled_time=now.time()
            )

        # Attach schedule to connection
        connection.schedule = job
        connection.save(update_fields=["schedule"])

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
            "client_profile": client_data
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

#         landscaper = request.user.landscaperprofilies
#         if job.landscaper != landscaper:
#             return Response(
#                 {"detail": "You are not assigned to this job"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Update schedule
#         if "scheduled_date" in request.data:
#             job.scheduled_date = request.data["scheduled_date"]

#         if "scheduled_time" in request.data:
#             job.scheduled_time = request.data["scheduled_time"]

#         # Mark as completed
#         if request.data.get("is_completed") in [True, "true", "True"]:
#             if not job.is_completed:
#                 job.is_completed = True
#                 job.completed_at = timezone.now()

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

#         # Serialize images correctly
#         image_urls = [img.image.url for img in job.images.all()]

#         return Response({
#             "job_id": job.id,
#             "service": job.service.name,
#             "scheduled_date": job.scheduled_date,
#             "scheduled_time": job.scheduled_time,
#             "is_completed": job.is_completed,
#             "completed_at": job.completed_at,
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

    def patch(self, request, job_id):
        job = get_object_or_404(ServiceSchedule, id=job_id)

        #  Only assigned landscaper can update
        landscaper = request.user.landscaperprofilies
        if job.landscaper != landscaper:
            return Response(
                {"detail": "You are not assigned to this job"},
                status=status.HTTP_403_FORBIDDEN
            )

        #  Update schedule fields
        if "scheduled_date" in request.data:
            job.scheduled_date = request.data["scheduled_date"]

        if "scheduled_time" in request.data:
            job.scheduled_time = request.data["scheduled_time"]

        #  Mark job as completed
        if request.data.get("is_completed") in [True, "true", "True"]:
            if not job.is_completed:
                job.is_completed = True
                job.completed_at = timezone.now()

        # Save ONE completion note (job-level)
        if "completion_note" in request.data:
            job.completion_note = request.data["completion_note"]

        job.save()

        #  Upload images ONLY after completion
        images = request.FILES.getlist("images")

        if images:
            if not job.is_completed:
                return Response(
                    {"error": "Complete the job before uploading images"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for image in images:
                ScheduleCompletionImage.objects.create(
                    schedule=job,
                    image=image
                )

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
            "payment_status": "pending" if job.is_completed else None,
            "images": image_urls,
            "client": ClientProfileSerializer(
                job.client,
                context={"request": request}
            ).data
        })
