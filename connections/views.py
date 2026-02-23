
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
from django.utils import timezone
# 
from django.db import transaction
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from profiles.models import LandscaperProfilies, ClientProfile
from services.models import ClientService, ServiceSchedule
from landscapers.models import Service
from connections.models import ConnectionRequest
from profiles.serializers import ClientProfileSerializer
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from datetime import timedelta

from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from subscriptions.models import Subscription 

from common.permissions import IsClient  # Optional: client-only permission
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied

from profiles.models import LandscaperProfilies, ClientProfile
from landscapers.models import Service
# from subscriptions. models import subscription 

from profiles.serializers import ClientProfileSerializer
from django.db.models import Q
from datetime import timedelta
from django.utils.timezone import now

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



# inbox/views.py
class InboxConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch all pending connection requests where the logged-in user is the receiver.
        Adds `sent_since` to indicate how long ago the request was sent.
        """
        # 1️⃣ Get all pending requests for the current user
        pending_requests = ConnectionRequest.objects.filter(
            receiver=request.user,
            is_accepted__isnull=True
        ).order_by("-created_at")  # newest first

        response = []

        for req in pending_requests:
            sender = req.sender
            sender_data = {"user_id": sender.id, "email": sender.email, "type": "unknown"}

            #  Check if sender is a landscaper
            try:
                sender_profile = sender.landscaperprofilies
                sender_data = LandscaperProfileSerializer(sender_profile, context={"request": request}).data
                sender_data["type"] = "landscaper"
            except LandscaperProfilies.DoesNotExist:
                #  Check if sender is a client
                try:
                    sender_profile = sender.clientprofile
                    sender_data = ClientProfileSerializer(sender_profile, context={"request": request}).data
                    sender_data["type"] = "client"
                except ClientProfile.DoesNotExist:
                    pass  # keep as "unknown"

            #  Calculate how long ago the request was sent
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
                # fallback to date string
                sent_since = req.created_at.strftime("%Y-%m-%d")

            #  Append request data to response
            response.append({
                "connection_id": req.id,
                "sent_by": sender_data,
                "created_at": req.created_at,
                "sent_since": sent_since,  
                "status": "pending"
            })

        #  Return all pending requests with `sent_since`
        return Response(response)



class SentConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ConnectionRequest.objects.filter(
            sender=request.user
        ).order_by("-created_at")

        return Response(ConnectionRequestDetailSerializer(qs, many=True).data)




class RespondConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user

        # Fetch the connection request
        connection = get_object_or_404(ConnectionRequest, id=pk)

        # Already responded check
        if connection.is_accepted is not None:
            return Response(
                {"detail": "This connection request has already been responded to."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check user is part of the connection
        if user not in (connection.sender, connection.receiver):
            return Response(
                {"detail": "You are not part of this request."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Determine roles
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
            return Response(
                {"detail": "Invalid user role."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate action
        action = request.data.get("action")
        if action not in ["accept", "reject"]:
            return Response(
                {"detail": "Invalid action."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reject request
        if action == "reject":
            connection.is_accepted = False
            connection.save(update_fields=["is_accepted"])
            return Response(
                {
                    "connection_id": connection.id,
                    "status": "rejected",
                    "responded_by": responder_role
                }
            )

        # -------------------------
        # Accept request
        # -------------------------

        # Count accepted connections for landscaper
        accepted_connections_count = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=landscaper_profile.user) |
            Q(receiver=landscaper_profile.user)
        ).count()

        plan_name = landscaper_profile.plan.name.lower() if landscaper_profile.plan else "free"

        if plan_name == "basic" and accepted_connections_count >= 10:
            return Response(
                {
                    "detail": "Basic landscapers can connect with up to 10 clients only. Upgrade to PRO for unlimited connections."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Accept connection
        connection.is_accepted = True
        connection.save(update_fields=["is_accepted"])

        # Ensure client has only one accepted landscaper
        if responder_role == "client":
            ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=user) | Q(receiver=user)
            ).exclude(id=connection.id).delete()

        # -------------------------
        # Fetch or create ClientService for scheduling
        # -------------------------
        service_obj = Service.objects.filter(
            landscaper=landscaper_profile.user
        ).order_by("-created_at").first()

        if not service_obj:
            # Undo connection acceptance
            connection.is_accepted = None
            connection.save(update_fields=["is_accepted"])
            return Response(
                {"detail": "This landscaper has not created any services yet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create ClientService instance if needed
        client_service, created = ClientService.objects.get_or_create(
            landscaper=landscaper_profile,
            name=service_obj.custom_service or (service_obj.standard_services[0] if service_obj.standard_services else "Service"),
            defaults={
                "description": service_obj.description,
                "category": service_obj.category,
                "price": service_obj.price or 0,
                "square_feet": service_obj.per_square_feet or 0,
                "is_standard": False
            }
        )

        # -------------------------
        # Create or fetch upcoming job
        # -------------------------
        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_profile,
            is_completed=False
        ).first()

        if not job:
            now = timezone.now()
            job = ServiceSchedule.objects.create(
                client=client_profile,
                landscaper=landscaper_profile,
                service=client_service,  # ✅ Correct ClientService instance
                scheduled_date=now.date(),
                scheduled_time=now.time()
            )

        # Link schedule to connection
        connection.schedule = job
        connection.save(update_fields=["schedule"])

        # Connection slot info for BASIC plan
        remaining_slots = None
        connection_warning = None
        if plan_name == "basic":
            MAX_CONNECTIONS = 10
            remaining_slots = MAX_CONNECTIONS - (accepted_connections_count + 1)
            if remaining_slots == 2:
                connection_warning = "You have used 8 out of 10 client connections. Consider upgrading to PRO."
            elif remaining_slots == 1:
                connection_warning = "You have only 1 client connection remaining. Upgrade to PRO to avoid limits."

        # Serialize client profile
        # Serialize both profiles
        client_data = ClientProfileSerializer(client_profile, context={"request": request}).data
        landscaper_data = LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data

        return Response(
            {
                "connection_id": connection.id,
                "status": "accepted",
                "accepted_by": responder_role,
                "upcoming_job": {
                    "job_id": job.id,
                    "date": job.scheduled_date,
                    "time": job.scheduled_time
                },
                "client_profile": client_data,
                "landscaper_profile": landscaper_data,
                "connection_limits": {
                    "plan": plan_name,
                    "accepted_connections": accepted_connections_count + 1,
                    "remaining_slots": remaining_slots,
                    "warning": connection_warning
                }
            },
            status=status.HTTP_200_OK
        )



class CancelConnectionRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Only allow cancelling own pending request
            connection = ConnectionRequest.objects.get(
                id=pk,
                sender=request.user,
                is_accepted__isnull=True   # still pending
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


# Accepted Connections / Auto Schedule

class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Get accepted connections for current user
        connections = ConnectionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_accepted=True
        ).select_related("sender", "receiver", "schedule").order_by("-created_at")

        response_data = []

        for conn in connections:
            other_user = conn.receiver if conn.sender == user else conn.sender

            # Connected time
            diff = now - conn.created_at
            if diff.days > 0:
                connected_since = f"{diff.days} days ago"
            elif diff.seconds >= 3600:
                connected_since = f"{diff.seconds // 3600} hours ago"
            elif diff.seconds >= 60:
                connected_since = f"{diff.seconds // 60} minutes ago"
            else:
                connected_since = "Just now"

            # Profiles
            landscaper_profile = LandscaperProfilies.objects.filter(user=other_user).first()
            client_profile = ClientProfile.objects.filter(user=other_user).first()

            if landscaper_profile:
                role = "landscaper"
                profile_data = LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data
            elif client_profile:
                role = "client"
                profile_data = ClientProfileSerializer(client_profile, context={"request": request}).data
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
                "connected_since": connected_since,
                "upcoming_job": upcoming_job
            })

        total_connections = len(response_data)

        # ---------------------------
        # Active percentage calculation
        # ---------------------------
        first_day_this_month = now.replace(day=1)
        first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)

        # Active users this month
        active_users_this_month = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_this_month
        ).values_list('receiver', 'sender')

        # Active users last month
        active_users_last_month = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_last_month,
            created_at__lte=last_day_last_month
        ).values_list('receiver', 'sender')

        # Flatten and deduplicate
        active_this = set([u for pair in active_users_this_month for u in pair])
        active_last = set([u for pair in active_users_last_month for u in pair])

        # Total active users (clients or landscapers depending on context)
        total_users = User.objects.filter(is_active=True).count()

        # Percentages
        active_percentage = (len(active_this) / total_users * 100) if total_users > 0 else 0
        previous_month_percentage = (len(active_last) / total_users * 100) if total_users > 0 else 0

        # Change vs previous month
        change_value = active_percentage - previous_month_percentage
        if change_value > 0:
            change_vs_last_month = f"+{change_value:.1f}"
        elif change_value < 0:
            change_vs_last_month = f"{change_value:.1f}"
        else:
            change_vs_last_month = "0.0"

        # ------------------------------
        # Connection limits
        # ------------------------------
        connection_limits = None
        landscaper_profile_self = LandscaperProfilies.objects.filter(user=user).first()

        if landscaper_profile_self:
            subscription = Subscription.objects.filter(user=user, is_active=True).first()
            plan_name = subscription.plan if subscription else "BASIC"

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
            else:
                connection_limits = {
                    "plan": "PRO",
                    "accepted_connections": accepted_count,
                    "max_connections": None,
                    "remaining_slots": None
                }

        # Final response
        return Response({
            "count": total_connections,
            "connections": response_data,
            "active_percentage": round(active_percentage, 1),
            "previous_month_percentage": round(previous_month_percentage, 1),
            "change_vs_last_month": change_vs_last_month,
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

# class RemoveConnectionAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, pk):
#         connection = get_object_or_404(
#             ConnectionRequest,
#             id=pk,
#             is_accepted=True
#         )

#         if request.user not in [connection.sender, connection.receiver]:
#             return Response(
#                 {"detail": "Permission denied"},
#                 status=403
#             )

#         connection.delete()
#         return Response(
#             {"message": "Connection removed"}
#         )


class RemoveConnectionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, connection_id):
        """
        Deletes a connection request or an accepted connection.
        - `connection_id` must be the ID of the ConnectionRequest.
        - Only the sender or receiver can remove the connection.
        """
        connection = get_object_or_404(ConnectionRequest, id=connection_id)

        if request.user not in [connection.sender, connection.receiver]:
            return Response({"detail": "Permission denied"}, status=403)

        connection.delete()
        return Response({"message": "Connection removed"}, status=200)

        

# job details and update by landscapers



class JobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLandscaper]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    def get_job_response(self, job, request):
        """
        Standardized response for both GET and PATCH
        """
        completed_services = job.completed_services.all()
        total_price = sum(s.price for s in completed_services)

        before_images = [img.image.url for img in job.images.filter(image_type="before")]
        after_images = [img.image.url for img in job.images.filter(image_type="after")]

        client_profile_image = None
        if hasattr(job.client, "image") and job.client.image:
            client_profile_image = job.client.image.url

        client_data = {
            "id": job.client.id,
            "name": getattr(job.client, "name", ""),
            "email": getattr(job.client.user, "email", ""),
            "phone": getattr(job.client, "phone", ""),
            "address": getattr(job.client, "address", ""),
            "profile_image": client_profile_image
        }

        return {
            "job_id": job.id,
            "service": job.service.name,
            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,
            "is_completed": job.is_completed,
            "completed_at": job.completed_at,
            "completion_note": job.completion_note,
            "payment_status": job.payment_status,
            "total_price": total_price,
            "completed_services": [
                {"id": s.id, "name": s.name, "price": s.price} for s in completed_services
            ],
            "before_images": before_images,
            "after_images": after_images,
            "client": client_data
        }
    def get(self, request, job_id):
        job = get_object_or_404(ServiceSchedule, id=job_id)
        return Response(self.get_job_response(job, request), status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request, job_id):
        job = get_object_or_404(ServiceSchedule, id=job_id)
        landscaper = getattr(request.user, "landscaperprofilies", None)

        # Restrict: only assigned landscaper can edit
        if not landscaper or job.landscaper != landscaper:
            return Response({"detail": "You are not assigned to this job"}, status=403)

        # Restrict: cannot update if job is already completed
        if job.is_completed:
            return Response({"detail": "This job is already marked as completed"}, status=400)

        # Update schedule if provided
        scheduled_date = request.data.get("scheduled_date")
        scheduled_time = request.data.get("scheduled_time")
        if scheduled_date:
            job.scheduled_date = scheduled_date
        if scheduled_time:
            job.scheduled_time = scheduled_time

        # Services completed
        service_ids = request.data.get("service_ids", [])
        completed_services = ClientService.objects.filter(id__in=service_ids, is_standard=True) if service_ids else []

        # Completion note
        note = request.data.get("completion_note", "")
        job.completion_note = note

        # Mark as completed if requested
        mark_done = request.data.get("is_completed", False)
        if mark_done:
            job.is_completed = True
            job.completed_at = timezone.now()

        job.save(update_fields=["scheduled_date", "scheduled_time", "completion_note", "is_completed", "completed_at"])

        # Save completed services
        if completed_services:
            job.completed_services.set(completed_services)

        # Save images if provided
        for img in request.FILES.getlist("before_images"):
            ScheduleCompletionImage.objects.create(schedule=job, image=img, image_type="before")
        for img in request.FILES.getlist("after_images"):
            ScheduleCompletionImage.objects.create(schedule=job, image=img, image_type="after")

        # TODO: auto-schedule next job if needed here (recurring logic)

        return Response(self.get_job_response(job, request), status=status.HTTP_200_OK)


class UpcomingServicesForClientAPIView(APIView):
    """
    Returns all pending services for the logged-in client.
    Shows landscaper profile and service details for each service.
    """
    permission_classes = [IsClient]  # Add IsClient if available

    def get(self, request):
        # 1️⃣ Get logged-in client profile
        try:
            client = request.user.clientprofile
        except ClientProfile.DoesNotExist:
            return Response([])

        # 2️⃣ Fetch all pending services for this client
        services = ServiceSchedule.objects.filter(
            client=client,
            is_completed=False
        ).select_related("landscaper", "service").order_by("scheduled_date", "scheduled_time")

        response = []

        for service in services:
            landscaper_profile = getattr(service.landscaper, "landscaperprofilies", None)
            if not landscaper_profile:
                continue  # skip if landscaper profile is missing

            # 3️⃣ Ensure the service is linked to an accepted connection
            connection_exists = ConnectionRequest.objects.filter(
                is_accepted=True
            ).filter(
                Q(sender=request.user, receiver=service.landscaper.user) |
                Q(sender=service.landscaper.user, receiver=request.user)
            ).exists()

            if not connection_exists:
                continue  # skip services without accepted connection

            # 4️⃣ Append service info with landscaper
            response.append({
                "service_id": service.id,
                "scheduled_date": service.scheduled_date,
                "scheduled_time": service.scheduled_time,
                "service": {
                    "id": service.service.id,
                    "name": service.service.name,
                    "description": service.service.description,
                    "category": service.service.category,
                    "price": float(service.service.price or 0),
                    "square_feet": service.service.square_feet
                },
                "landscaper": LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data
            })

        return Response(response)




# get+update+details

class ClientUpcomingServiceAPIView(APIView):
    """
    Returns upcoming services for the logged-in client.
    Client can reschedule and add a note.
    """
    permission_classes = [IsClient]

    def get(self, request, service_id=None):
        client = getattr(request.user, "clientprofile", None)
        if not client:
            return Response({"detail": "Not a client"}, status=403)

        if service_id:
            # Return details for a specific upcoming service
            service = get_object_or_404(ServiceSchedule, id=service_id, client=client, is_completed=False)
            response = {
                "service_id": service.id,
                "service_name": service.service.name,
                "scheduled_date": service.scheduled_date,
                "scheduled_time": service.scheduled_time,
                "client_note": getattr(service, "client_note", ""),
                "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
            }
            return Response(response)

        # Otherwise, return all upcoming services
        services = ServiceSchedule.objects.filter(
            client=client,
            is_completed=False
        ).select_related("landscaper", "service").order_by("scheduled_date", "scheduled_time")

        response = []
        for service in services:
            response.append({
                "service_id": service.id,
                "service_name": service.service.name,
                "scheduled_date": service.scheduled_date,
                "scheduled_time": service.scheduled_time,
                "client_note": getattr(service, "client_note", ""),
                "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
            })

        return Response(response)

    def patch(self, request, service_id):
        client = getattr(request.user, "clientprofile", None)
        if not client:
            return Response({"detail": "Not a client"}, status=403)

        service = get_object_or_404(ServiceSchedule, id=service_id, client=client, is_completed=False)

        scheduled_date = request.data.get("scheduled_date")
        scheduled_time = request.data.get("scheduled_time")
        client_note = request.data.get("client_note", "")

        if scheduled_date:
            service.scheduled_date = scheduled_date
        if scheduled_time:
            service.scheduled_time = scheduled_time
        service.client_note = client_note
        service.save(update_fields=["scheduled_date", "scheduled_time", "client_note"])

        return Response({
            "service_id": service.id,
            "service_name": service.service.name,
            "scheduled_date": service.scheduled_date,
            "scheduled_time": service.scheduled_time,
            "client_note": service.client_note,
            "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
        })

# class ClientCompletedServiceAPIView(APIView):
#     """
#     Returns all completed services for the logged-in client.
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         client = getattr(request.user, "clientprofile", None)
#         if not client:
#             return Response({"detail": "Not a client"}, status=403)

#         completed_services = ServiceSchedule.objects.filter(
#             client=client,
#             is_completed=True
#         ).select_related("landscaper", "service").order_by("-completed_at")

#         response = []
#         for service in completed_services:
#             response.append({
#                 "service_id": service.id,
#                 "service_name": service.service.name,
#                 "scheduled_date": service.scheduled_date,
#                 "scheduled_time": service.scheduled_time,
#                 "completion_note": getattr(service, "completion_note", ""),
#                 "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
#             })

#         return Response(response)




class ClientCompletedServiceAPIView(APIView):
    """
    Returns all completed services for the logged-in client.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = getattr(request.user, "clientprofile", None)
        if not client:
            return Response({"detail": "Not a client"}, status=403)

        completed_services = ServiceSchedule.objects.filter(
            client=client,
            is_completed=True
        ).select_related("landscaper", "service").order_by("-completed_at")

        response = []
        for service in completed_services:
            response.append({
                "service_id": service.id,
                "service_name": service.service.name,
                "scheduled_date": service.scheduled_date,
                "scheduled_time": service.scheduled_time,
                "completion_note": getattr(service, "completion_note", ""),
                "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
            })

        return Response(response)

# routes


from profiles.models import ClientProfile
from connections.models import ConnectionRequest
from accounts.models import User


class ConnectedClientListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get(self, request):
        user = request.user
        search_query = request.GET.get("search", "").strip()

        # ---------------------------------
        # Base Query: Only accepted connections
        # ---------------------------------
        connections = ConnectionRequest.objects.filter(
            is_accepted=True
        ).filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related("sender", "receiver")

        # ---------------------------------
        # DB-Level Search Filtering
        # ---------------------------------
        if search_query:
            connections = connections.filter(
                Q(sender__name__icontains=search_query) |
                Q(sender__email__icontains=search_query) |
                Q(sender__address__icontains=search_query) |
                Q(receiver__name__icontains=search_query) |
                Q(receiver__email__icontains=search_query) |
                Q(receiver__address__icontains=search_query)
            )

        clients_data = []

        for conn in connections:
            other_user = conn.receiver if conn.sender == user else conn.sender

            # Ensure the other user is a client
            try:
                client_profile = ClientProfile.objects.select_related("user").get(user=other_user)
            except ClientProfile.DoesNotExist:
                continue

            clients_data.append({
                "connection_id": conn.id,
                "client_id": other_user.id,
                "name": other_user.name,
                # "profile_image":other_user.image, 
                "profile_image": client_profile.image.url if client_profile.image else None,
                "email": other_user.email,
                "phone": other_user.phone,
                "address": getattr(other_user, "address", None),
                "latitude": getattr(other_user, "latitude", None),
                "longitude": getattr(other_user, "longitude", None),
                "connected_at": conn.created_at
            })

        return Response({
            "count": len(clients_data),
            "clients": clients_data
        }, status=status.HTTP_200_OK)

        

# todas job

class TodayJobsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLandscaper]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_job_response(self, job):
        """
        Standardized job response
        """
        completed_services = job.completed_services.all()
        total_price = sum(s.price for s in completed_services)

        before_images = [img.image.url for img in job.images.filter(image_type="before")]
        after_images = [img.image.url for img in job.images.filter(image_type="after")]

        client_data = {
            "id": job.client.id,
            "name": getattr(job.client, "name", ""),
            "email": job.client.user.email,
            "phone": getattr(job.client, "phone", ""),
            "address": getattr(job.client.user, "address", ""),
            "profile_image": getattr(job.client, "image", None).url if getattr(job.client, "image", None) else None
        }

        return {
            "job_id": job.id,
            "service": job.service.name,
            "scheduled_date": job.scheduled_date,
            "scheduled_time": job.scheduled_time,
            "is_completed": job.is_completed,
            "completed_at": job.completed_at,
            "completion_note": job.completion_note,
            "payment_status": job.payment_status,
            "total_price": total_price,
            "completed_services": [
                {"id": s.id, "name": s.name, "price": s.price} for s in completed_services
            ],
            "before_images": before_images,
            "after_images": after_images,
            "client": client_data
        }

    def get(self, request):
        landscaper = getattr(request.user, "landscaperprofilies", None)
        if not landscaper:
            return Response({"detail": "You are not a landscaper"}, status=403)

        now = timezone.now()

        # Filter jobs scheduled for today (works for DateField or DateTimeField)
        todays_jobs = ServiceSchedule.objects.filter(
            landscaper=landscaper,
            scheduled_date__year=now.year,
            scheduled_date__month=now.month,
            scheduled_date__day=now.day
        ).order_by("scheduled_time")

        response_data = [self.get_job_response(job) for job in todays_jobs]

        return Response({
            "count": len(response_data),
            "jobs": response_data
        }, status=status.HTTP_200_OK)