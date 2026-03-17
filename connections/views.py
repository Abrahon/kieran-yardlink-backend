
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from services.models import ServiceSchedule ,ClientService
# from rest_framework.exceptions import ValidationError
# from accounts.models import User
# from .models import ConnectionRequest
# from .serializers import (
#     ConnectionRequestDetailSerializer,
#     SendConnectionRequestSerializer,
#     RespondConnectionRequestSerializer,
#     AcceptedConnectionSerializer,
# )
# from rest_framework import serializers
# from django.contrib.auth import get_user_model
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from profiles.models import ClientProfile, LandscaperProfilies
# from landscapers.models import WorkingHours,Service
# from datetime import datetime, timedelta
# from django.utils.timezone import make_aware
# from django.db import transaction
# from rest_framework.exceptions import PermissionDenied
from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer
# from django.db.models import Q
# from rest_framework import status
# from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
# from services.models import ServiceSchedule, ScheduleCompletionImage
# from common.permissions import IsLandscaper
# from django.db.models import Q
# from profiles.serializers import ConnectedUserSerializer
# from django.utils import timezone
# # 
# from django.db import transaction
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.db.models import Q
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated

# from profiles.models import LandscaperProfilies, ClientProfile
# from services.models import ClientService, ServiceSchedule
# from landscapers.models import Service
# from connections.models import ConnectionRequest
# from profiles.serializers import ClientProfileSerializer
# from django.db.models import Q
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated

# from django.utils import timezone
# from datetime import timedelta

# from django.utils import timezone
# from django.db.models import Q
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from subscriptions.models import Subscription 

# from common.permissions import IsClient  # Optional: client-only permission
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.db.models import Q
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.exceptions import ValidationError, PermissionDenied

# from profiles.models import LandscaperProfilies, ClientProfile
# from subscriptions.models import Subscription, SubscriptionStatus

# from landscapers.models import Service,BusinessProfile
# # from subscriptions. models import subscription 

# from profiles.serializers import ClientProfileSerializer
# from django.db.models import Q
# from datetime import timedelta
# from django.utils.timezone import now

# User = get_user_model()



# # class SendConnectionRequestAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def post(self, request):
# #         serializer = SendConnectionRequestSerializer(
# #             data=request.data,
# #             context={"request": request}
# #         )
# #         serializer.is_valid(raise_exception=True)

# #         receiver = User.objects.get(
# #             id=serializer.validated_data["receiver_id"]
# #         )

# #         connection = ConnectionRequest.objects.create(
# #             sender=request.user,
# #             receiver=receiver
# #         )

# #         return Response(
# #             ConnectionRequestDetailSerializer(
# #                 connection,
# #                 context={"request": request}
# #             ).data,
# #             status=status.HTTP_201_CREATED
# #         )

# class SendConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = SendConnectionRequestSerializer(
#             data=request.data,
#             context={"request": request}
#         )
#         serializer.is_valid(raise_exception=True)

#         receiver = User.objects.get(
#             id=serializer.validated_data["receiver_id"]
#         )

#         # Create the connection request
#         connection = ConnectionRequest.objects.create(
#             sender=request.user,
#             receiver=receiver
#         )

#         # Get receiver profile safely
#         profile_data = self._get_profile(receiver)

#         return Response(
#             {
#                 "connection_id": connection.id,
#                 "receiver_profile": profile_data
#             },
#             status=status.HTTP_201_CREATED
#         )

#     def _get_profile(self, user):
#         business_profile = getattr(user, "landscaper_profile", None)
#         if business_profile:
#             return LandscaperProfileSerializer(business_profile, context={"request": self.request}).data

#         client_profile = getattr(user, "client_profile", None)
#         if client_profile:
#             return ClientProfileSerializer(client_profile, context={"request": self.request}).data

#         print(f"DEBUG: No profile found for user {user.id} ({user.email})")  # <-- debug line
#         return {}

# # inbox/views.py
# class InboxConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """
#         Fetch all pending connection requests where the logged-in user is the receiver.
#         Adds `sent_since` to indicate how long ago the request was sent.
#         """
#         # 1️⃣ Get all pending requests for the current user
#         pending_requests = ConnectionRequest.objects.filter(
#             receiver=request.user,
#             is_accepted__isnull=True
#         ).order_by("-created_at")  # newest first

#         response = []

#         for req in pending_requests:
#             sender = req.sender
#             sender_data = {"user_id": sender.id, "email": sender.email, "type": "unknown"}

#             #  Check if sender is a landscaper
#             try:
#                 sender_profile = sender.landscaperprofilies
#                 sender_data = LandscaperProfileSerializer(sender_profile, context={"request": request}).data
#                 sender_data["type"] = "landscaper"
#             except LandscaperProfilies.DoesNotExist:
#                 #  Check if sender is a client
#                 try:
#                     sender_profile = sender.clientprofile
#                     sender_data = ClientProfileSerializer(sender_profile, context={"request": request}).data
#                     sender_data["type"] = "client"
#                 except ClientProfile.DoesNotExist:
#                     pass  # keep as "unknown"

#             #  Calculate how long ago the request was sent
#             delta = now() - req.created_at
#             if delta < timedelta(minutes=1):
#                 sent_since = "just now"
#             elif delta < timedelta(hours=1):
#                 minutes = int(delta.total_seconds() // 60)
#                 sent_since = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
#             elif delta < timedelta(days=1):
#                 hours = int(delta.total_seconds() // 3600)
#                 sent_since = f"{hours} hour{'s' if hours != 1 else ''} ago"
#             elif delta < timedelta(days=7):
#                 days = delta.days
#                 sent_since = f"{days} day{'s' if days != 1 else ''} ago"
#             else:
#                 # fallback to date string
#                 sent_since = req.created_at.strftime("%Y-%m-%d")

#             #  Append request data to response
#             response.append({
#                 "connection_id": req.id,
#                 "sent_by": sender_data,
#                 "created_at": req.created_at,
#                 "sent_since": sent_since,  
#                 "status": "pending"
#             })

#         #  Return all pending requests with `sent_since`
#         return Response(response)



# # class SentConnectionRequestAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def get(self, request):
# #         qs = ConnectionRequest.objects.filter(
# #             sender=request.user
# #         ).order_by("-created_at")

# #         return Response(ConnectionRequestDetailSerializer(qs, many=True).data)

# class SentConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         qs = ConnectionRequest.objects.filter(sender=request.user).order_by("-created_at")
#         return Response(
#             ConnectionRequestDetailSerializer(
#                 qs, many=True, context={"request": request}
#             ).data
#         )


# # class RespondConnectionRequestAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     @transaction.atomic
# #     def post(self, request, pk):
# #         user = request.user

# #         # Fetch the connection request
# #         connection = get_object_or_404(ConnectionRequest, id=pk)

# #         # Already responded check
# #         if connection.is_accepted is not None:
# #             return Response(
# #                 {"detail": "This connection request has already been responded to."},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )

# #         # Check user is part of the connection
# #         if user not in (connection.sender, connection.receiver):
# #             return Response(
# #                 {"detail": "You are not part of this request."},
# #                 status=status.HTTP_403_FORBIDDEN
# #             )
# #         if user.role == "client":
# #             responder_role = "client"

# #             client_profile = get_object_or_404(ClientProfile, user=user)
# #             landscaper_profile = get_object_or_404(BusinessProfile, user=connection.receiver)

# #         elif user.role == "landscaper":
# #             responder_role = "landscaper"

# #             landscaper_profile = get_object_or_404(BusinessProfile, user=user)
# #             client_profile = get_object_or_404(ClientProfile, user=connection.sender)

# #         else:
# #             return Response({"detail": "Invalid user role."}, status=400)
            
            
# #         # Validate action
# #         action = request.data.get("action")
# #         if action not in ["accept", "reject"]:
# #             return Response(
# #                 {"detail": "Invalid action."},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )

# #         # Reject request
# #         if action == "reject":
# #             connection.is_accepted = False
# #             connection.save(update_fields=["is_accepted"])
# #             return Response(
# #                 {
# #                     "connection_id": connection.id,
# #                     "status": "rejected",
# #                     "responded_by": responder_role
# #                 }
# #             )

# #         # -------------------------
# #         # Accept request
# #         # -------------------------

# #         # Count accepted connections for landscaper
# #         accepted_connections_count = ConnectionRequest.objects.filter(
# #             is_accepted=True
# #         ).filter(
# #             Q(sender=landscaper_profile.user) |
# #             Q(receiver=landscaper_profile.user)
# #         ).count()



# #         plan_name = landscaper_profile.plan.name.lower() if landscaper_profile.plan else "free"

# #         if plan_name == "basic" and accepted_connections_count >= 10:
# #             return Response(
# #                 {
# #                     "detail": "Basic landscapers can connect with up to 10 clients only. Upgrade to PRO for unlimited connections."
# #                 },
# #                 status=status.HTTP_403_FORBIDDEN
# #             )

# #         # Accept connection
# #         connection.is_accepted = True
# #         connection.save(update_fields=["is_accepted"])

# #         # Ensure client has only one accepted landscaper
# #         if responder_role == "client":
# #             ConnectionRequest.objects.filter(
# #                 is_accepted=True
# #             ).filter(
# #                 Q(sender=user) | Q(receiver=user)
# #             ).exclude(id=connection.id).delete()


# #         # -------------------------
# #         # Fetch or create ClientService for scheduling
# #         # -------------------------
# #         service_obj = Service.objects.filter(
# #             business=landscaper_profile   # ✅ FIXED
# #         ).order_by("-created_at").first()

# #         if not service_obj:
# #             connection.is_accepted = None
# #             connection.save(update_fields=["is_accepted"])
# #             return Response(
# #                 {"detail": "This landscaper has not created any services yet."},
# #                 status=status.HTTP_400_BAD_REQUEST
# #             )

        
# #         client_service, created = ClientService.objects.get_or_create(
# #             landscaper=landscaper_profile,
# #             name=service_obj.standard_service or "Service",
# #             defaults={
# #                 "description": service_obj.description or "", 
# #                 "category": service_obj.category,
# #                 "price": service_obj.price or 0,
# #                 "square_feet": getattr(service_obj, "per_square_feet", 0),
# #                 "is_standard": service_obj.category == "standard"
# #             }
# #         )

# #         # -------------------------
# #         # Create or fetch upcoming job
# #         # -------------------------
# #         job = ServiceSchedule.objects.filter(
# #             client=client_profile,
# #             landscaper=landscaper_profile,
# #             is_completed=False
# #         ).first()

# #         if not job:
# #             now = timezone.now()
# #             job = ServiceSchedule.objects.create(
# #                 client=client_profile,
# #                 landscaper=landscaper_profile,
# #                 service=client_service, 
# #                 scheduled_date=now.date(),
# #                 scheduled_time=now.time()
# #             )

# #         # Link schedule to connection
# #         connection.schedule = job
# #         connection.save(update_fields=["schedule"])

# #         # Connection slot info for BASIC plan
# #         remaining_slots = None
# #         connection_warning = None
# #         if plan_name == "basic":
# #             MAX_CONNECTIONS = 10
# #             remaining_slots = MAX_CONNECTIONS - (accepted_connections_count + 1)
# #             if remaining_slots == 2:
# #                 connection_warning = "You have used 8 out of 10 client connections. Consider upgrading to PRO."
# #             elif remaining_slots == 1:
# #                 connection_warning = "You have only 1 client connection remaining. Upgrade to PRO to avoid limits."

# #         # Serialize client profile
# #         # Serialize both profiles
# #         client_data = ClientProfileSerializer(client_profile, context={"request": request}).data
# #         landscaper_data = LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data

# #         return Response(
# #             {
# #                 "connection_id": connection.id,
# #                 "status": "accepted",
# #                 "accepted_by": responder_role,
# #                 "upcoming_job": {
# #                     "job_id": job.id,
# #                     "date": job.scheduled_date,
# #                     "time": job.scheduled_time
# #                 },
# #                 "client_profile": client_data,
# #                 "landscaper_profile": landscaper_data,
# #                 "connection_limits": {
# #                     "plan": plan_name,
# #                     "accepted_connections": accepted_connections_count + 1,
# #                     "remaining_slots": remaining_slots,
# #                     "warning": connection_warning
# #                 }
# #             },
# #             status=status.HTTP_200_OK
# #         )

# # from django.db import transaction
# # from django.utils import timezone
# # from django.db.models import Q
# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework import status
# # from rest_framework.permissions import IsAuthenticated
# # from django.shortcuts import get_object_or_404

# # from connections.models import ConnectionRequest, ClientService, ServiceSchedule
# # from profiles.models import ClientProfile, LandscaperProfilies
# # from landscapers.models import BusinessProfile, Service
# # from subscriptions.models import Subscription
# # from profiles.serializers import ClientProfileSerializer, LandscaperProfileSerializer


# class RespondConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request, pk):
#         user = request.user

#         # Fetch connection request
#         connection = get_object_or_404(ConnectionRequest, id=pk)

#         # Already responded check
#         if connection.is_accepted is not None:
#             return Response(
#                 {"detail": "This connection request has already been responded to."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # User must be part of connection
#         if user not in (connection.sender, connection.receiver):
#             return Response(
#                 {"detail": "You are not part of this request."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # -------------------------
#         # Determine roles and profiles
#         # -------------------------
#         if user.role == "client":
#             responder_role = "client"
#             client_profile = get_object_or_404(ClientProfile, user=user)
#             landscaper_business = get_object_or_404(BusinessProfile, user=connection.receiver)
#             landscaper_profile = get_object_or_404(LandscaperProfilies, user=connection.receiver)

#         elif user.role == "landscaper":
#             responder_role = "landscaper"
#             client_profile = get_object_or_404(ClientProfile, user=connection.sender)
#             landscaper_business = get_object_or_404(BusinessProfile, user=user)
#             landscaper_profile = get_object_or_404(LandscaperProfilies, user=user)

#         else:
#             return Response({"detail": "Invalid user role."}, status=400)

#         # -------------------------
#         # Validate action
#         # -------------------------
#         action = request.data.get("action")
#         if action not in ["accept", "reject"]:
#             return Response({"detail": "Invalid action."}, status=400)

#         # -------------------------
#         # Reject request
#         # -------------------------
#         if action == "reject":
#             connection.is_accepted = False
#             connection.save(update_fields=["is_accepted"])
#             return Response({
#                 "connection_id": connection.id,
#                 "status": "rejected",
#                 "responded_by": responder_role
#             })

#         # -------------------------
#         # Accept request
#         # -------------------------

#         # Count accepted connections for landscaper
#         accepted_connections_count = ConnectionRequest.objects.filter(
#             is_accepted=True
#         ).filter(
#             Q(sender=landscaper_profile.user) | Q(receiver=landscaper_profile.user)
#         ).count()

#         # -------------------------
#         # Determine plan
#         # -------------------------
#         now = timezone.now()
#         subscription = (
#             Subscription.objects
#             .filter(user=landscaper_profile.user, is_active=True)
#             .order_by("-end_date")
#             .first()
#         )

#         if subscription and subscription.status.lower() == "active" and subscription.end_date >= now:
#             plan_name = subscription.plan.name.lower()
#         elif landscaper_profile.plan:
#             plan_name = landscaper_profile.plan.name.lower()
#         else:
#             plan_name = "free"

#         # Enforce basic plan limit
#         if plan_name == "basic" and accepted_connections_count >= 10:
#             return Response(
#                 {
#                     "detail": "Basic landscapers can connect with up to 10 clients only. Upgrade to PRO for unlimited connections."
#                 },
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         # Accept the connection
#         connection.is_accepted = True
#         connection.save(update_fields=["is_accepted"])

#         # Ensure client has only one accepted landscaper
#         if responder_role == "client":
#             ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=user) | Q(receiver=user)
#             ).exclude(id=connection.id).delete()

#         # -------------------------
#         # Fetch or create ClientService
#         # -------------------------
#         service_obj = Service.objects.filter(
#             business=landscaper_business
#         ).order_by("-created_at").first()

#         if not service_obj:
#             connection.is_accepted = None
#             connection.save(update_fields=["is_accepted"])
#             return Response(
#                 {"detail": "This landscaper has not created any services yet."},
#                 status=400
#             )

#         client_service, created = ClientService.objects.get_or_create(
#             landscaper=landscaper_profile,
#             name=getattr(service_obj, "standard_service", "Service"),
#             defaults={
#                 "description": service_obj.description or "",
#                 "category": getattr(service_obj, "category", "general"),
#                 "price": getattr(service_obj, "base_price", 0) or 0,
#                 "square_feet": getattr(service_obj, "per_square_feet", 0),
#                 "is_standard": getattr(service_obj, "category", None) == "standard"
#             }
#         )

#         # -------------------------
#         # Create or fetch upcoming job
#         # -------------------------
#         job = ServiceSchedule.objects.filter(
#             client=client_profile,
#             landscaper=landscaper_profile,
#             is_completed=False
#         ).first()

#         if not job:
#             now = timezone.now()
#             job = ServiceSchedule.objects.create(
#                 client=client_profile,
#                 landscaper=landscaper_profile,
#                 service=client_service,
#                 scheduled_date=now.date(),
#                 scheduled_time=now.time()
#             )

#         # Link schedule to connection
#         connection.schedule = job
#         connection.save(update_fields=["schedule"])

#         # -------------------------
#         # Connection slot info for BASIC plan
#         # -------------------------
#         remaining_slots = None
#         connection_warning = None
#         if plan_name == "basic":
#             MAX_CONNECTIONS = 10
#             remaining_slots = MAX_CONNECTIONS - (accepted_connections_count + 1)
#             if remaining_slots == 2:
#                 connection_warning = "You have used 8 out of 10 client connections. Consider upgrading to PRO."
#             elif remaining_slots == 1:
#                 connection_warning = "You have only 1 client connection remaining. Upgrade to PRO to avoid limits."

#         # -------------------------
#         # Serialize profiles
#         # -------------------------
#         client_data = ClientProfileSerializer(client_profile, context={"request": request}).data
#         landscaper_data = LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data

#         return Response({
#             "connection_id": connection.id,
#             "status": "accepted",
#             "accepted_by": responder_role,
#             "upcoming_job": {
#                 "job_id": job.id,
#                 "date": job.scheduled_date,
#                 "time": job.scheduled_time
#             },
#             "client_profile": client_data,
#             "landscaper_profile": landscaper_data,
#             "connection_limits": {
#                 "plan": plan_name,
#                 "accepted_connections": accepted_connections_count + 1,
#                 "remaining_slots": remaining_slots,
#                 "warning": connection_warning
#             }
#         }, status=status.HTTP_200_OK)

# class CancelConnectionRequestAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, pk):
#         try:
#             # Only allow cancelling own pending request
#             connection = ConnectionRequest.objects.get(
#                 id=pk,
#                 sender=request.user,
#                 is_accepted__isnull=True   # still pending
#             )
#         except ConnectionRequest.DoesNotExist:
#             return Response(
#                 {"error": "Request not found or cannot be cancelled"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         connection.delete()

#         return Response(
#             {"message": "Request cancelled successfully"},
#             status=status.HTTP_200_OK
#         )


# # # Accepted Connections / Auto Schedule
# # class AcceptedConnectionsAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def get(self, request):
# #         user = request.user
# #         now = timezone.now()

# #         # Get accepted connections for current user
# #         connections = ConnectionRequest.objects.filter(
# #             Q(sender=user) | Q(receiver=user),
# #             is_accepted=True
# #         ).select_related("sender", "receiver", "schedule").order_by("-created_at")

# #         response_data = []

# #         for conn in connections:
# #             other_user = conn.receiver if conn.sender == user else conn.sender

# #             # Connected time
# #             diff = now - conn.created_at
# #             if diff.days > 0:
# #                 connected_since = f"{diff.days} days ago"
# #             elif diff.seconds >= 3600:
# #                 connected_since = f"{diff.seconds // 3600} hours ago"
# #             elif diff.seconds >= 60:
# #                 connected_since = f"{diff.seconds // 60} minutes ago"
# #             else:
# #                 connected_since = "Just now"

# #             # Profiles
# #             landscaper_profile = LandscaperProfilies.objects.filter(user=other_user).first()
# #             client_profile = ClientProfile.objects.filter(user=other_user).first()

# #             if landscaper_profile:
# #                 role = "landscaper"
# #                 profile_data = LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data
# #             elif client_profile:
# #                 role = "client"
# #                 profile_data = ClientProfileSerializer(client_profile, context={"request": request}).data
# #             else:
# #                 continue

# #             # Upcoming job
# #             upcoming_job = None
# #             if conn.schedule:
# #                 upcoming_job = {
# #                     "job_id": conn.schedule.id,
# #                     "service_name": conn.schedule.service.name,
# #                     "date": conn.schedule.scheduled_date,
# #                     "time": conn.schedule.scheduled_time,
# #                     "price": conn.schedule.service.price,
# #                     "payment_status": conn.schedule.payment_status,
# #                 }

# #             response_data.append({
# #                 "connection_id": conn.id,
# #                 "connected_user": {
# #                     "id": other_user.id,
# #                     "name": getattr(other_user, "name", ""),
# #                     "email": other_user.email,
# #                     "role": role,
# #                 },
# #                 "profile": profile_data,
# #                 "connected_at": conn.created_at,
# #                 "connected_since": connected_since,
# #                 "upcoming_job": upcoming_job
# #             })

# #         total_connections = len(response_data)

# #         # ---------------------------
# #         # Active percentage calculation
# #         # ---------------------------
# #         first_day_this_month = now.replace(day=1)
# #         first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
# #         last_day_last_month = first_day_this_month - timedelta(days=1)

# #         # Active users this month
# #         active_users_this_month = ConnectionRequest.objects.filter(
# #             is_accepted=True,
# #             created_at__gte=first_day_this_month
# #         ).values_list('receiver', 'sender')

# #         # Active users last month
# #         active_users_last_month = ConnectionRequest.objects.filter(
# #             is_accepted=True,
# #             created_at__gte=first_day_last_month,
# #             created_at__lte=last_day_last_month
# #         ).values_list('receiver', 'sender')

# #         # Flatten and deduplicate
# #         active_this = set([u for pair in active_users_this_month for u in pair])
# #         active_last = set([u for pair in active_users_last_month for u in pair])

# #         # Total active users (clients or landscapers depending on context)
# #         total_users = User.objects.filter(is_active=True).count()

# #         # Percentages
# #         active_percentage = (len(active_this) / total_users * 100) if total_users > 0 else 0
# #         previous_month_percentage = (len(active_last) / total_users * 100) if total_users > 0 else 0

# #         # Change vs previous month
# #         change_value = active_percentage - previous_month_percentage
# #         if change_value > 0:
# #             change_vs_last_month = f"+{change_value:.1f}"
# #         elif change_value < 0:
# #             change_vs_last_month = f"{change_value:.1f}"
# #         else:
# #             change_vs_last_month = "0.0"

# #         # ------------------------------
# #         # Connection limits
# #         # ------------------------------
# #         connection_limits = None
# #         landscaper_profile_self = LandscaperProfilies.objects.filter(user=user).first()

# #         if landscaper_profile_self:
# #             subscription = Subscription.objects.filter(user=user, is_active=True).first()
# #             plan_name = subscription.plan if subscription else "BASIC"

# #             accepted_count = ConnectionRequest.objects.filter(
# #                 is_accepted=True
# #             ).filter(
# #                 Q(sender=user) | Q(receiver=user)
# #             ).count()

# #             if plan_name == "BASIC":
# #                 connection_limits = {
# #                     "plan": "BASIC",
# #                     "accepted_connections": accepted_count,
# #                     "max_connections": 10,
# #                     "remaining_slots": max(0, 10 - accepted_count)
# #                 }
# #             else:
# #                 connection_limits = {
# #                     "plan": "PRO",
# #                     "accepted_connections": accepted_count,
# #                     "max_connections": None,
# #                     "remaining_slots": None
# #                 }

# #         # Final response
# #         return Response({
# #             "count": total_connections,
# #             "connections": response_data,
# #             "active_percentage": round(active_percentage, 1),
# #             "previous_month_percentage": round(previous_month_percentage, 1),
# #             "change_vs_last_month": change_vs_last_month,
# #             "connection_limits": connection_limits
# #         })

# from datetime import timedelta
# from django.utils import timezone
# from django.db.models import Q
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response

# from subscriptions.models import  Subscription, SubscriptionStatus
# from connections.models import ConnectionRequest
# from profiles.serializers import LandscaperProfileSerializer, ClientProfileSerializer
# from jobs .serializers import JobSerializer


# # Accepted Connections / Auto Schedule
# class AcceptedConnectionsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         now = timezone.now()

#         # Get accepted connections for current user
#         connections = ConnectionRequest.objects.filter(
#             Q(sender=user) | Q(receiver=user),
#             is_accepted=True
#         ).select_related("sender", "receiver", "schedule").order_by("-created_at")

#         response_data = []

#         for conn in connections:
#             other_user = conn.receiver if conn.sender == user else conn.sender

#             # Connected time
#             diff = now - conn.created_at
#             if diff.days > 0:
#                 connected_since = f"{diff.days} days ago"
#             elif diff.seconds >= 3600:
#                 connected_since = f"{diff.seconds // 3600} hours ago"
#             elif diff.seconds >= 60:
#                 connected_since = f"{diff.seconds // 60} minutes ago"
#             else:
#                 connected_since = "Just now"

#             # -------------------------------
#             # Get profile data
#             # -------------------------------
#             landscaper_profile = getattr(other_user, "landscaper_profile", None)
#             client_profile = getattr(other_user, "client_profile", None)

#             if landscaper_profile:
#                 role = "landscaper"
#                 try:
#                     business_profile = landscaper_profile.user.landscaper_profile
#                 except BusinessProfile.DoesNotExist:
#                     business_profile = None

#                 profile_data = (
#                     LandscaperProfileSerializer(business_profile, context={"request": request}).data
#                     if business_profile else {}
#                 )

#             elif client_profile:
#                 role = "client"
#                 profile_data = ClientProfileSerializer(client_profile, context={"request": request}).data
#             else:
#                 continue

#             # -------------------------------
#             # Upcoming job
#             # -------------------------------
#             upcoming_job = None
#             if conn.schedule:
#                 upcoming_job = {
#                     "job_id": conn.schedule.id,
#                     "service_name": conn.schedule.service.name if conn.schedule.service else None,
#                     "date": conn.schedule.scheduled_date,
#                     "time": conn.schedule.scheduled_time,
#                     "price": getattr(conn.schedule.service, "base_price", None),
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
#                 "upcoming_job": upcoming_job
#             })

#         total_connections = len(response_data)

#         # ---------------------------
#         # Active percentage calculation
#         # ---------------------------
#         first_day_this_month = now.replace(day=1)
#         first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
#         last_day_last_month = first_day_this_month - timedelta(days=1)

#         # Active users this month
#         active_users_this_month = ConnectionRequest.objects.filter(
#             is_accepted=True,
#             created_at__gte=first_day_this_month
#         ).values_list('receiver', 'sender')

#         # Active users last month
#         active_users_last_month = ConnectionRequest.objects.filter(
#             is_accepted=True,
#             created_at__gte=first_day_last_month,
#             created_at__lte=last_day_last_month
#         ).values_list('receiver', 'sender')

#         # Flatten and deduplicate
#         active_this = set([u for pair in active_users_this_month for u in pair])
#         active_last = set([u for pair in active_users_last_month for u in pair])

#         total_users = user.__class__.objects.filter(is_active=True).count()

#         active_percentage = (len(active_this) / total_users * 100) if total_users > 0 else 0
#         previous_month_percentage = (len(active_last) / total_users * 100) if total_users > 0 else 0

#         change_value = active_percentage - previous_month_percentage
#         if change_value > 0:
#             change_vs_last_month = f"+{change_value:.1f}"
#         elif change_value < 0:
#             change_vs_last_month = f"{change_value:.1f}"
#         else:
#             change_vs_last_month = "0.0"

#         # ------------------------------
#         # Connection limits (for landscapers)
#         # ------------------------------
#         connection_limits = None
#         landscaper_profile_self = getattr(user, "landscaper_profile", None)

#         if landscaper_profile_self:
#             subscription = Subscription.objects.filter(user=user, is_active=True).first()
#             plan_name = subscription.plan.name.upper() if subscription else "BASIC"

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
#                     "remaining_slots": max(0, 10 - accepted_count)
#                 }
#             else:
#                 connection_limits = {
#                     "plan": "PRO",
#                     "accepted_connections": accepted_count,
#                     "max_connections": None,
#                     "remaining_slots": None
#                 }

#         # ------------------------------
#         # Final response
#         # ------------------------------
#         return Response({
#             "count": total_connections,
#             "connections": response_data,
#             "active_percentage": round(active_percentage, 1),
#             "previous_month_percentage": round(previous_month_percentage, 1),
#             "change_vs_last_month": change_vs_last_month,
#             "connection_limits": connection_limits
#         })
# # -------------------------------
# # Upcoming Job
# # -------------------------------

# from common.permissions import IsLandscaper
# class UpcomingJobListAPIView(APIView):
#     """
#     Returns all pending jobs for the logged-in landscaper.
#     Shows client profile for each job.
#     """
#     permission_classes = [IsAuthenticated, IsLandscaper]

#     def get(self, request):
#         # 1️⃣ Get logged-in landscaper profile
#         try:
#             landscaper = request.user.landscaperprofilies
#         except LandscaperProfilies.DoesNotExist:
#             return Response([])

#         # 2️⃣ Fetch all pending jobs assigned to this landscaper
#         jobs = ServiceSchedule.objects.filter(
#             landscaper=landscaper,
#             is_completed=False
#         ).select_related("client", "service").order_by("scheduled_date", "scheduled_time")

#         response = []

#         for job in jobs:
#             client_profile = job.client

#             # 3️⃣ Ensure the job is linked to an accepted connection
#             connection_exists = ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=client_profile.user, receiver=request.user) |
#                 Q(sender=request.user, receiver=client_profile.user)
#             ).exists()

#             if not connection_exists:
#                 continue  # skip jobs without accepted connection

#             # 4️⃣ Append job info
#             response.append({
#                 "job_id": job.id,
#                 "service_name": job.service.name,
#                 "scheduled_date": job.scheduled_date,
#                 "scheduled_time": job.scheduled_time,
#                 "price": float(job.service.price or 0),
#                 "client": ClientProfileSerializer(client_profile, context={"request": request}).data
#             })

#         return Response(response)

# # class RemoveConnectionAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def delete(self, request, pk):
# #         connection = get_object_or_404(
# #             ConnectionRequest,
# #             id=pk,
# #             is_accepted=True
# #         )

# #         if request.user not in [connection.sender, connection.receiver]:
# #             return Response(
# #                 {"detail": "Permission denied"},
# #                 status=403
# #             )

# #         connection.delete()
# #         return Response(
# #             {"message": "Connection removed"}
# #         )


# class RemoveConnectionAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, connection_id):
#         """
#         Deletes a connection request or an accepted connection.
#         - `connection_id` must be the ID of the ConnectionRequest.
#         - Only the sender or receiver can remove the connection.
#         """
#         connection = get_object_or_404(ConnectionRequest, id=connection_id)

#         if request.user not in [connection.sender, connection.receiver]:
#             return Response({"detail": "Permission denied"}, status=403)

#         connection.delete()
#         return Response({"message": "Connection removed"}, status=200)

        

# # job details and update by landscapers



# class JobDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsLandscaper]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]
#     def get_job_response(self, job, request):
#         """
#         Standardized response for both GET and PATCH
#         """
#         completed_services = job.completed_services.all()
#         total_price = sum(s.price for s in completed_services)

#         before_images = [img.image.url for img in job.images.filter(image_type="before")]
#         after_images = [img.image.url for img in job.images.filter(image_type="after")]

#         client_profile_image = None
#         if hasattr(job.client, "image") and job.client.image:
#             client_profile_image = job.client.image.url

#         client_data = {
#             "id": job.client.id,
#             "name": getattr(job.client, "name", ""),
#             "email": getattr(job.client.user, "email", ""),
#             "phone": getattr(job.client, "phone", ""),
#             "address": getattr(job.client, "address", ""),
#             "profile_image": client_profile_image
#         }

#         return {
#             "job_id": job.id,
#             "service": job.service.name,
#             "scheduled_date": job.scheduled_date,
#             "scheduled_time": job.scheduled_time,
#             "is_completed": job.is_completed,
#             "completed_at": job.completed_at,
#             "completion_note": job.completion_note,
#             "payment_status": job.payment_status,
#             "total_price": total_price,
#             "completed_services": [
#                 {"id": s.id, "name": s.name, "price": s.price} for s in completed_services
#             ],
#             "before_images": before_images,
#             "after_images": after_images,
#             "client": client_data
#         }
#     def get(self, request, job_id):
#         job = get_object_or_404(ServiceSchedule, id=job_id)
#         return Response(self.get_job_response(job, request), status=status.HTTP_200_OK)

#     @transaction.atomic
#     def patch(self, request, job_id):
#         job = get_object_or_404(ServiceSchedule, id=job_id)
#         landscaper = getattr(request.user, "landscaperprofilies", None)

#         # Restrict: only assigned landscaper can edit
#         if not landscaper or job.landscaper != landscaper:
#             return Response({"detail": "You are not assigned to this job"}, status=403)

#         # Restrict: cannot update if job is already completed
#         if job.is_completed:
#             return Response({"detail": "This job is already marked as completed"}, status=400)

#         # Update schedule if provided
#         scheduled_date = request.data.get("scheduled_date")
#         scheduled_time = request.data.get("scheduled_time")
#         if scheduled_date:
#             job.scheduled_date = scheduled_date
#         if scheduled_time:
#             job.scheduled_time = scheduled_time

#         # Services completed
#         service_ids = request.data.get("service_ids", [])
#         completed_services = ClientService.objects.filter(id__in=service_ids, is_standard=True) if service_ids else []

#         # Completion note
#         note = request.data.get("completion_note", "")
#         job.completion_note = note

#         # Mark as completed if requested
#         mark_done = request.data.get("is_completed", False)
#         if mark_done:
#             job.is_completed = True
#             job.completed_at = timezone.now()

#         job.save(update_fields=["scheduled_date", "scheduled_time", "completion_note", "is_completed", "completed_at"])

#         # Save completed services
#         if completed_services:
#             job.completed_services.set(completed_services)

#         # Save images if provided
#         for img in request.FILES.getlist("before_images"):
#             ScheduleCompletionImage.objects.create(schedule=job, image=img, image_type="before")
#         for img in request.FILES.getlist("after_images"):
#             ScheduleCompletionImage.objects.create(schedule=job, image=img, image_type="after")

#         # TODO: auto-schedule next job if needed here (recurring logic)

#         return Response(self.get_job_response(job, request), status=status.HTTP_200_OK)


# class UpcomingServicesForClientAPIView(APIView):
#     """
#     Returns all pending services for the logged-in client.
#     Shows landscaper profile and service details for each service.
#     """
#     permission_classes = [IsClient]  

#     def get(self, request):
#         #  Get logged-in client profile
#         try:
#             client = request.user.clientprofile
#         except ClientProfile.DoesNotExist:
#             return Response([])

#         #  Fetch all pending services for this client
#         services = ServiceSchedule.objects.filter(
#             client=client,
#             is_completed=False
#         ).select_related("landscaper", "service").order_by("scheduled_date", "scheduled_time")

#         response = []

#         for service in services:
#             landscaper_profile = getattr(service.landscaper, "landscaperprofilies", None)
#             if not landscaper_profile:
#                 continue  # skip if landscaper profile is missing

#             #  Ensure the service is linked to an accepted connection
#             connection_exists = ConnectionRequest.objects.filter(
#                 is_accepted=True
#             ).filter(
#                 Q(sender=request.user, receiver=service.landscaper.user) |
#                 Q(sender=service.landscaper.user, receiver=request.user)
#             ).exists()

#             if not connection_exists:
#                 continue  # skip services without accepted connection

#             #  Append service info with landscaper
#             response.append({
#                 "service_id": service.id,
#                 "scheduled_date": service.scheduled_date,
#                 "scheduled_time": service.scheduled_time,
#                 "service": {
#                     "id": service.service.id,
#                     "name": service.service.name,
#                     "description": service.service.description,
#                     "category": service.service.category,
#                     "price": float(service.service.price or 0),
#                     "square_feet": service.service.square_feet
#                 },
#                 "landscaper": LandscaperProfileSerializer(landscaper_profile, context={"request": request}).data
#             })

#         return Response(response)




# # get+update+details

# class ClientUpcomingServiceAPIView(APIView):
#     """
#     Returns upcoming services for the logged-in client.
#     Client can reschedule and add a note.
#     """
#     permission_classes = [IsClient]

#     def get(self, request, service_id=None):
#         client = getattr(request.user, "clientprofile", None)
#         if not client:
#             return Response({"detail": "Not a client"}, status=403)

#         if service_id:
#             # Return details for a specific upcoming service
#             service = get_object_or_404(ServiceSchedule, id=service_id, client=client, is_completed=False)
#             response = {
#                 "service_id": service.id,
#                 "service_name": service.service.name,
#                 "scheduled_date": service.scheduled_date,
#                 "scheduled_time": service.scheduled_time,
#                 "client_note": getattr(service, "client_note", ""),
#                 "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
#             }
#             return Response(response)

#         # Otherwise, return all upcoming services
#         services = ServiceSchedule.objects.filter(
#             client=client,
#             is_completed=False
#         ).select_related("landscaper", "service").order_by("scheduled_date", "scheduled_time")

#         response = []
#         for service in services:
#             response.append({
#                 "service_id": service.id,
#                 "service_name": service.service.name,
#                 "scheduled_date": service.scheduled_date,
#                 "scheduled_time": service.scheduled_time,
#                 "client_note": getattr(service, "client_note", ""),
#                 "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
#             })

#         return Response(response)

#     def patch(self, request, service_id):
#         client = getattr(request.user, "clientprofile", None)
#         if not client:
#             return Response({"detail": "Not a client"}, status=403)

#         service = get_object_or_404(ServiceSchedule, id=service_id, client=client, is_completed=False)

#         scheduled_date = request.data.get("scheduled_date")
#         scheduled_time = request.data.get("scheduled_time")
#         client_note = request.data.get("client_note", "")

#         if scheduled_date:
#             service.scheduled_date = scheduled_date
#         if scheduled_time:
#             service.scheduled_time = scheduled_time
#         service.client_note = client_note
#         service.save(update_fields=["scheduled_date", "scheduled_time", "client_note"])

#         return Response({
#             "service_id": service.id,
#             "service_name": service.service.name,
#             "scheduled_date": service.scheduled_date,
#             "scheduled_time": service.scheduled_time,
#             "client_note": service.client_note,
#             "landscaper": LandscaperProfileSerializer(service.landscaper, context={"request": request}).data
#         })

# # class ClientUpcomingServiceAPIView(APIView):
# #     """
# #     Returns upcoming services for the logged-in client.
# #     Client can reschedule and add a note.
# #     """
# #     permission_classes = [IsClient]

# #     def get(self, request, service_id=None):
# #         # FIX 1: Properly get client profile
# #         try:
# #             client = request.user.clientprofile
# #         except AttributeError:
# #             return Response({"detail": "Not a client"}, status=403)

# #         # FIX 2: Ensure landscaper & service loaded properly
# #         queryset = ServiceSchedule.objects.filter(
# #             client=client,
# #             is_completed=False
# #         ).select_related("landscaper", "service").order_by(
# #             "scheduled_date", "scheduled_time"
# #         )

# #         # If specific service requested
# #         if service_id:
# #             service = get_object_or_404(queryset, id=service_id)

# #             # FIX 3: Safe service name handling
# #             service_name = getattr(service.service, "name", None) or \
# #                            getattr(service.service, "standard_service", "Service")

# #             return Response({
# #                 "service_id": service.id,
# #                 "service_name": service_name,
# #                 "scheduled_date": service.scheduled_date,
# #                 "scheduled_time": service.scheduled_time,
# #                 "client_note": getattr(service, "client_note", ""),
# #                 "landscaper": LandscaperProfileSerializer(
# #                     service.landscaper,
# #                     context={"request": request}
# #                 ).data
# #             })

# #         # Otherwise return all upcoming
# #         response = []

# #         for schedule in queryset:

# #             # FIX 4: Ensure service exists
# #             if not schedule.service:
# #                 continue

# #             service_name = getattr(schedule.service, "name", None) or \
# #                            getattr(schedule.service, "standard_service", "Service")

# #             response.append({
# #                 "service_id": schedule.id,
# #                 "service_name": service_name,
# #                 "scheduled_date": schedule.scheduled_date,
# #                 "scheduled_time": schedule.scheduled_time,
# #                 "client_note": getattr(schedule, "client_note", ""),
# #                 "landscaper": LandscaperProfileSerializer(
# #                     schedule.landscaper,
# #                     context={"request": request}
# #                 ).data
# #             })

# #         return Response(response)

# #     def patch(self, request, service_id):
# #         # FIX 5: Proper client validation
# #         try:
# #             client = request.user.clientprofile
# #         except AttributeError:
# #             return Response({"detail": "Not a client"}, status=403)

# #         service = get_object_or_404(
# #             ServiceSchedule.objects.select_related("service", "landscaper"),
# #             id=service_id,
# #             client=client,
# #             is_completed=False
# #         )

# #         scheduled_date = request.data.get("scheduled_date")
# #         scheduled_time = request.data.get("scheduled_time")
# #         client_note = request.data.get("client_note")

# #         # FIX 6: Update only provided fields
# #         if scheduled_date:
# #             service.scheduled_date = scheduled_date

# #         if scheduled_time:
# #             service.scheduled_time = scheduled_time

# #         if client_note is not None:
# #             service.client_note = client_note

# #         service.save()

# #         service_name = getattr(service.service, "name", None) or \
# #                        getattr(service.service, "standard_service", "Service")

# #         return Response({
# #             "service_id": service.id,
# #             "service_name": service_name,
# #             "scheduled_date": service.scheduled_date,
# #             "scheduled_time": service.scheduled_time,
# #             "client_note": getattr(service, "client_note", ""),
# #             "landscaper": LandscaperProfileSerializer(
# #                 service.landscaper,
# #                 context={"request": request}
# #             ).data
# #         })



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

# # routes


# from profiles.models import ClientProfile
# from connections.models import ConnectionRequest
# from accounts.models import User


# class ConnectedClientListAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsLandscaper]

#     def get(self, request):
#         user = request.user
#         search_query = request.GET.get("search", "").strip()

#         # ---------------------------------
#         # Base Query: Only accepted connections
#         # ---------------------------------
#         connections = ConnectionRequest.objects.filter(
#             is_accepted=True
#         ).filter(
#             Q(sender=user) | Q(receiver=user)
#         ).select_related("sender", "receiver")

#         # ---------------------------------
#         # DB-Level Search Filtering
#         # ---------------------------------
#         if search_query:
#             connections = connections.filter(
#                 Q(sender__name__icontains=search_query) |
#                 Q(sender__email__icontains=search_query) |
#                 Q(sender__address__icontains=search_query) |
#                 Q(receiver__name__icontains=search_query) |
#                 Q(receiver__email__icontains=search_query) |
#                 Q(receiver__address__icontains=search_query)
#             )

#         clients_data = []

#         for conn in connections:
#             other_user = conn.receiver if conn.sender == user else conn.sender

#             # Ensure the other user is a client
#             try:
#                 client_profile = ClientProfile.objects.select_related("user").get(user=other_user)
#             except ClientProfile.DoesNotExist:
#                 continue

#             clients_data.append({
#                 "connection_id": conn.id,
#                 "client_id": other_user.id,
#                 "name": other_user.name,
#                 # "profile_image":other_user.image, 
#                 "profile_image": client_profile.image.url if client_profile.image else None,
#                 "email": other_user.email,
#                 "phone": other_user.phone,
#                 "address": getattr(other_user, "address", None),
#                 "latitude": getattr(other_user, "latitude", None),
#                 "longitude": getattr(other_user, "longitude", None),
#                 "connected_at": conn.created_at
#             })

#         return Response({
#             "count": len(clients_data),
#             "clients": clients_data
#         }, status=status.HTTP_200_OK)

        

# # todas job

# class TodayJobsAPIView(APIView):
#     permission_classes = [IsAuthenticated, IsLandscaper]
#     parser_classes = [JSONParser, MultiPartParser, FormParser]

#     def get_job_response(self, job):
#         """
#         Standardized job response
#         """
#         completed_services = job.completed_services.all()
#         total_price = sum(s.price for s in completed_services)

#         before_images = [img.image.url for img in job.images.filter(image_type="before")]
#         after_images = [img.image.url for img in job.images.filter(image_type="after")]

#         client_data = {
#             "id": job.client.id,
#             "name": getattr(job.client, "name", ""),
#             "email": job.client.user.email,
#             "phone": getattr(job.client, "phone", ""),
#             "address": getattr(job.client.user, "address", ""),
#             "profile_image": getattr(job.client, "image", None).url if getattr(job.client, "image", None) else None
#         }

#         return {
#             "job_id": job.id,
#             "service": job.service.name,
#             "scheduled_date": job.scheduled_date,
#             "scheduled_time": job.scheduled_time,
#             "is_completed": job.is_completed,
#             "completed_at": job.completed_at,
#             "completion_note": job.completion_note,
#             "payment_status": job.payment_status,
#             "total_price": total_price,
#             "completed_services": [
#                 {"id": s.id, "name": s.name, "price": s.price} for s in completed_services
#             ],
#             "before_images": before_images,
#             "after_images": after_images,
#             "client": client_data
#         }

#     def get(self, request):
#         landscaper = getattr(request.user, "landscaperprofilies", None)
#         if not landscaper:
#             return Response({"detail": "You are not a landscaper"}, status=403)

#         now = timezone.now()

#         # Filter jobs scheduled for today (works for DateField or DateTimeField)
#         todays_jobs = ServiceSchedule.objects.filter(
#             landscaper=landscaper,
#             scheduled_date__year=now.year,
#             scheduled_date__month=now.month,
#             scheduled_date__day=now.day
#         ).order_by("scheduled_time")

#         response_data = [self.get_job_response(job) for job in todays_jobs]

#         return Response({
#             "count": len(response_data),
#             "jobs": response_data
#         }, status=status.HTTP_200_OK)

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
from services.models import ServiceSchedule, ClientService, ScheduleCompletionImage
from subscriptions.models import Subscription, SubscriptionStatus

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
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from connections.models import ConnectionRequest
from profiles.models import ClientProfile, LandscaperProfilies


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
        job = ServiceSchedule.objects.filter(
            client=client_profile,
            landscaper=landscaper_basic,
            is_completed=False
        ).order_by("scheduled_date", "scheduled_time").first()

        if not job:
            current_time = timezone.now()
            job = ServiceSchedule.objects.create(
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


class AcceptedConnectionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_time = timezone.now()

        connections = ConnectionRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_accepted=True
        ).select_related(
            "sender", "receiver", "schedule"
        ).order_by("-created_at")

        response_data = []

        for conn in connections:
            other_user = conn.receiver if conn.sender == user else conn.sender

            diff = current_time - conn.created_at
            if diff.days > 0:
                connected_since = f"{diff.days} days ago"
            elif diff.seconds >= 3600:
                connected_since = f"{diff.seconds // 3600} hours ago"
            elif diff.seconds >= 60:
                connected_since = f"{diff.seconds // 60} minutes ago"
            else:
                connected_since = "Just now"

            business_profile = getattr(other_user, "landscaper_profile", None)
            client_profile = getattr(other_user, "client_profile", None)

            if business_profile:
                role = "landscaper"
                profile_data = LandscaperProfileSerializer(
                    business_profile,
                    context={"request": request}
                ).data
            elif client_profile:
                role = "client"
                profile_data = ClientProfileSerializer(
                    client_profile,
                    context={"request": request}
                ).data
            else:
                continue

            upcoming_job = None
            if conn.schedule:
                upcoming_job = {
                    "job_id": conn.schedule.id,
                    "service_name": getattr(conn.schedule.service, "name", None),
                    "date": conn.schedule.scheduled_date,
                    "time": conn.schedule.scheduled_time,
                    "price": float(getattr(conn.schedule.service, "price", 0) or 0),
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
                "upcoming_job": upcoming_job,
            })

        total_connections = len(response_data)

        first_day_this_month = current_time.replace(day=1)
        first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)

        active_users_this_month = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_this_month
        ).values_list("receiver", "sender")

        active_users_last_month = ConnectionRequest.objects.filter(
            is_accepted=True,
            created_at__gte=first_day_last_month,
            created_at__lte=last_day_last_month
        ).values_list("receiver", "sender")

        active_this = set(u for pair in active_users_this_month for u in pair)
        active_last = set(u for pair in active_users_last_month for u in pair)

        total_users = User.objects.filter(is_active=True).count()

        active_percentage = (len(active_this) / total_users * 100) if total_users > 0 else 0
        previous_month_percentage = (len(active_last) / total_users * 100) if total_users > 0 else 0

        change_value = active_percentage - previous_month_percentage
        if change_value > 0:
            change_vs_last_month = f"+{change_value:.1f}"
        elif change_value < 0:
            change_vs_last_month = f"{change_value:.1f}"
        else:
            change_vs_last_month = "0.0"

        connection_limits = None
        landscaper_business_self = getattr(user, "landscaper_profile", None)
        landscaper_basic_self = getattr(user, "landscaperprofilies", None)

        if landscaper_business_self:
            subscription = Subscription.objects.filter(
                user=user,
                is_active=True,
                status=SubscriptionStatus.ACTIVE
            ).select_related("plan").first()

            if subscription and subscription.plan:
                plan_name = subscription.plan.name.upper()
            elif landscaper_basic_self and landscaper_basic_self.plan:
                plan_name = landscaper_basic_self.plan.name.upper()
            else:
                plan_name = "BASIC"

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
                    "remaining_slots": max(0, 10 - accepted_count),
                }
            else:
                connection_limits = {
                    "plan": plan_name,
                    "accepted_connections": accepted_count,
                    "max_connections": None,
                    "remaining_slots": None,
                }

        return Response(
            {
                "count": total_connections,
                "connections": response_data,
                "active_percentage": round(active_percentage, 1),
                "previous_month_percentage": round(previous_month_percentage, 1),
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

#         todays_jobs = ServiceSchedule.objects.filter(
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