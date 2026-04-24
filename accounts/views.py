from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
# Create your views here.
from urllib.parse import urlencode, unquote
from .serializers import UserSerializer
import requests
from reviews.models import LandscaperReview
from django.db.models import Sum, Avg, FloatField, Value
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import views
from django.shortcuts import get_object_or_404
from .serializers import SignupSerializer, LoginSerializer, ResetPasswordSerializer,ResendOTPSerializer
from .models import User, OTP,UserReport
from django.utils import timezone
from .models import AdminAuditLog
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.models import User, LoginActivity
from accounts.models import LoginActivity  # add at top
from django.db.models import Avg, Q
from accounts.models import LoginActivity
# from jobs.models import Job, PaymentStatus
from django.db.models import Q, Sum, FloatField, Count
from django.shortcuts import get_object_or_404
from django.db.models import Sum, FloatField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from django.db.models import Sum, Value, FloatField, Avg
from django.db.models.functions import Coalesce


from subscriptions.models import Subscription
from landscapers.models import BusinessProfile
from profiles.models import LandscaperProfilies
from jobs.models import Job
from reviews.models import LandscaperReview
from .models import LoginActivity, AdminAuditLog

from .serializers import AdminUserDetailSerializer, AdminUserUpdateSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from subscriptions.models import Subscription

# ✅ BusinessProfile stays where it is (your landscapers app)
from landscapers.models import BusinessProfile

# ✅ LandscaperProfilies is in profiles app (as you said)
from profiles.models import LandscaperProfilies
from subscriptions.models import Subscription, SubscriptionStatus
from jobs.models import Job
from .utils import generate_otp, send_otp_email 
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer,VerifyOTPForgetSerializer,UserReportSerializer
)




class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data["email"]


        request.session["pending_user"] = {

            "email": data["email"],
            "name": data["name"],
            "password": data["password"],
            "phone": data.get("phone"),
            "address": data.get("address"),
            "latitude": str(data["latitude"]) if data.get("latitude") else None,
            "longitude": str(data["longitude"]) if data.get("longitude") else None,
            "role": data["role"],
            "allow_notification": data.get("allow_notification", False)
        }

        request.session.modified = True

        # OTP handling
        OTP.objects.filter(email=email).delete()
        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        send_otp_email(email, otp_code, data["name"])

        return Response(
            {"detail": f"Verification OTP sent to {data['role']} email."},
            status=200
        )


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    refresh['name'] = user.name 
    refresh['email'] = user.email
    refresh['phone'] = user.phone
    refresh['address'] = user.address

     # optional
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

from .serializers import LoginSerializer
from .models import User, OTP, LoginActivity
from .utils import generate_otp, send_otp_email
from .security_utils import get_client_ip, parse_device
from django.contrib.auth.models import update_last_login
# your existing function
from .views import get_tokens_for_user  


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        if not user.is_active:
            return Response(
                {"message": "Please verify your email first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔐 STEP 1 → If ADMIN → send OTP (do NOT log activity yet)
        # Because admin isn't fully authenticated until OTP verification succeeds.
        if user.role == "admin":
            OTP.objects.filter(user=user).delete()

            otp_code = generate_otp()
            OTP.objects.create(user=user, code=otp_code)

            send_otp_email(user.email, otp_code)

            return Response({
                "message": "OTP sent to admin email",
                "admin_2fa_required": True,
                "email": user.email
            }, status=status.HTTP_200_OK)

        # ✅ Normal users login directly
        tokens = get_tokens_for_user(user)

        # -------------------------
        # ✅ Update last_login
        # -------------------------
        User.objects.filter(id=user.id).update(last_login=timezone.now())

        # -------------------------
        # ✅ Create LoginActivity record
        # -------------------------
        # -------------------------
        # Create LoginActivity record (SAFE VERSION)
        # -------------------------

        ip = get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "") or ""

        device_info = parse_device(ua) or {}

        update_last_login(None, user)

        LoginActivity.objects.create(
            user=user,
            ip_address=ip,
            user_agent=ua,

            device_type=device_info.get("device_type") or "unknown",
            os=device_info.get("os") or "unknown",
            browser=device_info.get("browser") or "unknown",
        )


        return Response({
            "message": "Login successful",
            "token": tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "phone": getattr(user, "phone", None),
                "address": getattr(user, "address", None),
                "last_login":user.last_login,
                "latitude": float(user.latitude) if getattr(user, "latitude", None) else None,
                "longitude": float(user.longitude) if getattr(user, "longitude", None) else None,
            }
        }, status=status.HTTP_200_OK)




# create admin verify otp
class AdminVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")
        otp_code = request.data.get("otp")

        user = User.objects.filter(email=email, role="admin").first()

        if not user:
            return Response({"detail": "Admin not found"}, status=404)

        otp = OTP.objects.filter(user=user, code=otp_code).first()

        if not otp:
            return Response({"detail": "Invalid OTP"}, status=400)

        if otp.is_expired():
            return Response({"detail": "OTP expired"}, status=400)

        otp.delete()

        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Admin login successful",
            "token": tokens
        })


class SendOTPView(generics.CreateAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()  
        print("serializer.save() returned:", result)

        # ❌ ISSUE IS HERE:
        # serializer.save() is returning a User object, NOT a dict.
        # User object has NO .get() method — that's why error occurred:
        # AttributeError: 'User' object has no attribute 'get'

        email = serializer.validated_data.get("email")
        if email and hasattr(request, "session"):
            request.session['otp_user_email'] = email
            print("Stored in session:", email)

        return Response(
            {"message": "OTP sent successfully", "email": email},
            
            status=200
        )


# resend otp views 
class ResendOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # 🔁 Remove old OTPs
        OTP.objects.filter(email=email).delete()

        # 🔐 Generate new OTP
        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        # 📧 Send email
        send_otp_email(email, otp_code)

        # 🧠 Optional: store in session
        request.session["otp_user_email"] = email
        request.session.modified = True

        return Response(
            {"detail": "OTP resent successfully."},
            status=status.HTTP_200_OK
        )



# resend otp forget password
class ResendForgotOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Delete old OTPs for forgot password flow
        OTP.objects.filter(email=email).delete()

        # Generate new OTP
        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        # Send email
        send_otp_email(email, otp_code, subject="Forgot Password OTP")

        return Response(
            {"detail": "Forgot password OTP resent successfully."},
            status=status.HTTP_200_OK
        )


# verify otpo for email

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        otp_obj = OTP.objects.filter(email=email, code=otp).first()
        if not otp_obj:
            return Response(
                {"detail": "Invalid or expired OTP"},
                status=400
            )

        pending_user = request.session.get("pending_user")
        if not pending_user or pending_user["email"] != email:
            return Response(
                {"detail": "Session expired. Please signup again."},
                status=400
            )

        # ✅ CREATE USER WITH LAT & LNG SAVED
        user = User.objects.create_user(
            email=pending_user["email"],
            name=pending_user["name"],
            password=pending_user["password"],
            phone=pending_user.get("phone"),
            address=pending_user.get("address"),
            role=pending_user["role"],
            latitude=pending_user.get("latitude"),     
            longitude=pending_user.get("longitude"),
            is_active=True
        )

        # cleanup
        OTP.objects.filter(email=email).delete()
        request.session.flush()

        # tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "phone": user.phone,
                "address": user.address,
                "latitude": float(user.latitude) if user.latitude else None,
                "longitude": float(user.longitude) if user.longitude else None,
            }
        }, status=201)


# verify otp for forget password 
class VerifyOTPForgetView(generics.GenericAPIView):
    serializer_class = VerifyOTPForgetSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # OTP verified → keep email in session for password reset
        request.session['verified_email'] = serializer.validated_data["user"].email

        return Response({"message": "OTP verified successfully."})


# 
class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Request body must include:
        {
            "email": "user@example.com",
            "otp": "123456",
            "new_password": "newStrongPassword123",
            "confirm_password": "newStrongPassword123"
        }
        """
        email = request.data.get("email")
        otp_code = request.data.get("otp")
        print("otp_code",otp_code)

        if not email or not otp_code:
            return Response(
                {"detail": "Email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1️⃣ Verify user exists
        user = User.objects.filter(email=email).first()
        print("user", user)

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2️⃣ Verify OTP
        # otp = OTP.objects.filter(user=user, code=str(otp_code)).order_by("-created_at").first()
        otp = OTP.objects.filter(user=user, code=str(otp_code).strip()).order_by("-created_at").first()
        print("otp", otp)
        if not otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ OTP valid → delete OTP to prevent reuse
        otp.delete()

        # 4️⃣ Reset password
        serializer = self.get_serializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)


# resend otp for forget password
class ResendForgotOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Delete old OTPs for forgot password flow
        OTP.objects.filter(email=email).delete()

        # Generate new OTP
        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        # Send email
        send_otp_email(email, otp_code, subject="Forgot Password OTP")

        return Response(
            {"detail": "Forgot password OTP resent successfully."},
            status=status.HTTP_200_OK
        )


from datetime import timedelta
from django.db.models import (
    Q, Count, Sum, FloatField, Value, OuterRef, Subquery, Avg, IntegerField
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from accounts.models import User
from subscriptions.models import Subscription, SubscriptionStatus
from landscapers.models import BusinessProfile
from jobs.models import Job


class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        role = request.query_params.get("role")
        plan = request.query_params.get("plan")
        status_param = request.query_params.get("status")
        location = request.query_params.get("location")
        search_query = request.query_params.get("search", "").strip()
        sort_by = request.query_params.get("sort")

        users = User.objects.all()

        # --------------------------
        # FILTERS
        # --------------------------
        if role:
            users = users.filter(role__iexact=role)

        if status_param:
            if status_param.lower() == "paused":
                users = users.filter(is_active=False)
            elif status_param.lower() == "active":
                users = users.filter(is_active=True)

        if location:
            users = users.filter(address__icontains=location)

        if plan:
            users = users.filter(
                subscription__is_active=True,
                subscription__plan__name__iexact=plan
            )

        # --------------------------
        # SEARCH
        # --------------------------
        # if search_query:
        #     users = users.filter(
        #         Q(name__icontains=search_query) |
        #         Q(email__icontains=search_query) |
        #         Q(role__icontains=search_query) |
        #         Q(address__icontains=search_query) |
        #         Q(subscription__plan__name__icontains=search_query) |
        #         Q(subscription__status__icontains=search_query)
        #     )
            if search_query:
                users = users.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |   # partial email search
                    Q(email__iexact=search_query) |      # exact email match (faster hit)
                    Q(role__icontains=search_query) |
                    Q(address__icontains=search_query) |
                    Q(subscription__plan__name__icontains=search_query)
                )

        users = users.distinct()

        # ==========================================================
        # SUBQUERIES
        # ==========================================================

        business_profile_sq = BusinessProfile.objects.filter(
            user=OuterRef("pk")
        ).values("id")[:1]

        # ✅ Revenue (USE total_price)
        revenue_sq = Job.objects.filter(
            landscaper_id=Subquery(business_profile_sq),
            payment_status=Job.PaymentStatus.PAID
        ).values("landscaper_id").annotate(
            total=Sum("total_price", output_field=FloatField())
        ).values("total")[:1]

        # ✅ Total Jobs
        jobs_sq = Job.objects.filter(
            landscaper_id=Subquery(business_profile_sq)
        ).values("landscaper_id").annotate(
            total=Count("id")
        ).values("total")[:1]

        # ✅ Completed Jobs
        completed_jobs_sq = Job.objects.filter(
            landscaper_id=Subquery(business_profile_sq),
            status=Job.Status.COMPLETED
        ).values("landscaper_id").annotate(
            total=Count("id")
        ).values("total")[:1]

        # ✅ Total Clients (handles both client + external_client)
        clients_sq = Job.objects.filter(
            landscaper_id=Subquery(business_profile_sq)
        ).values("landscaper_id").annotate(
            total=Count("client_id", distinct=True) +
                  Count("external_client_id", distinct=True)
        ).values("total")[:1]

        # ==========================================================
        # ANNOTATIONS
        # ==========================================================

        users = users.annotate(
            total_revenue=Coalesce(Subquery(revenue_sq, output_field=FloatField()), Value(0.0)),
            total_jobs=Coalesce(Subquery(jobs_sq, output_field=IntegerField()), Value(0)),
            completed_jobs=Coalesce(Subquery(completed_jobs_sq, output_field=IntegerField()), Value(0)),
            total_clients=Coalesce(Subquery(clients_sq, output_field=IntegerField()), Value(0)),

            average_rating=Coalesce(
                Avg("received_reviews__rating"),
                Value(0.0),
                output_field=FloatField()
            ),
            review_count=Count("received_reviews", distinct=True)
        )

        # --------------------------
        # SORTING
        # --------------------------
        if sort_by == "revenue":
            users = users.order_by("-total_revenue")
        elif sort_by == "clients":
            users = users.order_by("-total_clients")
        elif sort_by == "jobs":
            users = users.order_by("-total_jobs")
        elif sort_by == "rating":
            users = users.order_by("-average_rating")
        else:
            users = users.order_by("-date_joined")

        # ==========================================================
        # PLATFORM METRICS
        # ==========================================================

        total_users = User.objects.count()
        total_clients = User.objects.filter(role="client").count()
        total_landscapers = User.objects.filter(role="landscaper").count()
        paused_users = User.objects.filter(is_active=False).count()
        active_users = User.objects.filter(is_active=True).count()

        last_24h = timezone.now() - timedelta(hours=24)
        daily_active_users = User.objects.filter(last_login__gte=last_24h).count()

        one_week_ago = timezone.now() - timedelta(days=7)
        weekly_new_signups = User.objects.filter(date_joined__gte=one_week_ago).count()

        # ✅ FIXED: Platform Revenue
        total_job_amount = Job.objects.filter(
            payment_status=Job.PaymentStatus.PAID
        ).aggregate(
            total=Sum("total_price", output_field=FloatField())
        )["total"] or 0.0

        platform_fee_collected = round(total_job_amount * 0.02, 2)

        # Subscriptions
        active_subscriptions = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE).count()
        cancelled_subscriptions = Subscription.objects.filter(status=SubscriptionStatus.CANCELLED).count()
        expired_subscriptions = Subscription.objects.filter(status=SubscriptionStatus.EXPIRED).count()

        total_subscription_pool = active_subscriptions + cancelled_subscriptions + expired_subscriptions

        churn_rate = round(
            ((cancelled_subscriptions + expired_subscriptions) / total_subscription_pool) * 100,
            2
        ) if total_subscription_pool > 0 else 0.0

        overall_average_rating = users.aggregate(
            avg_rating=Coalesce(
                Avg("received_reviews__rating"),
                Value(0.0),
                output_field=FloatField()
            )
        )["avg_rating"]

        # --------------------------
        # PAGINATION
        # --------------------------
        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(users, request)

        serializer = AdminUserDetailSerializer(page, many=True, context={"request": request})

        return paginator.get_paginated_response({
            "status": "success",
            "summary": {
                "total_users": total_users,
                "total_clients": total_clients,
                "total_landscapers": total_landscapers,
                "active_users": active_users,
                "paused_users": paused_users,
                "daily_active_users": daily_active_users,
                "weekly_new_signups": weekly_new_signups,
                "active_subscriptions": active_subscriptions,
                "cancelled_subscriptions": cancelled_subscriptions,
                "expired_subscriptions": expired_subscriptions,
                "churn_rate": churn_rate,
                "platform_fee_collected": platform_fee_collected,
                "average_rating": round(overall_average_rating, 2) if overall_average_rating else 0.0
            },
            "data": serializer.data
        })



class AdminUserSuspendView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        if request.user.id == user.id:
            return Response(
                {"status": "error", "message": "You cannot suspend your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_active = request.data.get("is_active")
        admin_notes = request.data.get("admin_notes")

        if is_active is None:
            return Response(
                {"status": "error", "message": "is_active is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(is_active, bool):
            return Response(
                {"status": "error", "message": "is_active must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = is_active
        update_fields = ["is_active"]

        if admin_notes is not None:
            user.admin_notes = admin_notes
            update_fields.append("admin_notes")

        user.save(update_fields=update_fields)

        return Response(
            {
                "status": "success",
                "message": "User updated successfully.",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "admin_notes": user.admin_notes,
                },
            },
            status=status.HTTP_200_OK,
        )

#    delete admins
class AdminDeleteUserView(generics.DestroyAPIView):
    """
    Admin can delete any user by ID.
    Users can delete their own account by confirming their password.
    Only superusers can delete other superusers.
    """
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        user_to_delete = self.get_object()

        # Check if the user is deleting their own account
        if request.user == user_to_delete:
            password = request.data.get("password")
            if not password:
                return Response(
                    {"detail": "Password is required to delete your account."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not check_password(password, user_to_delete.password):
                return Response(
                    {"detail": "Incorrect password."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Admin deletion rules
        elif not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to delete this user."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only superuser can delete another superuser
        if user_to_delete.is_superuser and not request.user.is_superuser:
            return Response(
                {"detail": "Only a superuser can delete another superuser."},
                status=status.HTTP_403_FORBIDDEN
            )

        email = user_to_delete.email
        target_user_id = user_to_delete.id

        # 🔐 Audit Log BEFORE delete
        AdminAuditLog.objects.create(
            admin=request.user,
            action="Delete User",
            target_user=user_to_delete,
            details=f"Admin {request.user.email} deleted user {email}"
        )

        user_to_delete.delete()


        return Response(
            {"detail": f"User {email} deleted successfully."},
            status=status.HTTP_200_OK
        )



class SelfDeleteUserView(generics.DestroyAPIView):
    """
    Authenticated user can delete their own account
    by providing their password.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get("password")

        if not password:
            return Response(
                {"detail": "Password is required to delete your account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not check_password(password, user.password):
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = user.email
        user.delete()

        return Response(
            {"detail": f"Account {email} deleted successfully."},
            status=status.HTTP_200_OK
        )

# user puse 

# class AdminPauseUserView(APIView):
#     """
#     Admin API to pause (deactivate) or unpause (activate) a user
#     """
#     permission_classes = [IsAdminUser]

#     def patch(self, request, user_id):
#         """
#         Toggle user's active status.
#         Send JSON payload: {"action": "pause"} or {"action": "unpause"}
#         """
#         user = get_object_or_404(User, id=user_id)

#         action = request.data.get("action")
#         if action not in ["pause", "unpause"]:
#             return Response(
#                 {"detail": "Invalid action. Must be 'pause' or 'unpause'."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if action == "pause":
#             user.is_active = False
#             message = "User has been paused."
#         else:
#             user.is_active = True
#             message = "User has been unpaused."

#         user.save(update_fields=["is_active"])
        
#         # 🔐 Create audit log
#         AdminAuditLog.objects.create(
#             admin=request.user,
#             action=action,
#             target_user=user,
#             details=f"Admin {request.user.email} performed '{log_action}' on {user.email}"
#         )

#         return Response(
#             {
#                 "status": "success",
#                 "message": message,
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "is_active": user.is_active,
#                 }
#             },
#             status=status.HTTP_200_OK
#         )

class AdminPauseUserView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        action = request.data.get("action")
        if action not in ["pause", "unpause"]:
            return Response(
                {"detail": "Invalid action. Must be 'pause' or 'unpause'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == "pause":
            user.is_active = False
            message = "User has been paused."
        else:
            user.is_active = True
            message = "User has been unpaused."

        user.save(update_fields=["is_active"])

        #  FIXED audit log
        AdminAuditLog.objects.create(
            admin=request.user,
            action=action,  
            target_user=user,
            details=f"Admin {request.user.email} performed '{action}' on {user.email}"
        )

        return Response(
            {
                "status": "success",
                "message": message,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "is_active": user.is_active,
                }
            },
            status=status.HTTP_200_OK
        )



# report views
# views.py
class ReportUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        reported_user = get_object_or_404(User, id=user_id)

        # Prevent self-report
        if request.user == reported_user:
            return Response(
                {"detail": "You cannot report yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        UserReport.objects.create(
            reporter=request.user,
            reported_user=reported_user,
            note=serializer.validated_data["note"]
        )

        return Response(
            {"message": "Report submitted successfully"},
            status=status.HTTP_201_CREATED
        )

class AdminAuditLogView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        logs = AdminAuditLog.objects.all().order_by("-created_at")

        data = []

        for log in logs:
            data.append({
                "admin": log.admin.email,
                "action": log.action,
                "target_user": log.target_user.email if log.target_user else None,
                "details": log.details,
                "time": log.created_at
            })

        return Response(data)


# user detaisl

class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # -------------------------
        # Subscription
        # -------------------------
        subscription = (
            Subscription.objects
            .select_related("plan")
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

        subscription_data = None
        if subscription:
            subscription_data = {
                "id": subscription.id,
                "status": subscription.status,
                "is_active": subscription.is_active,
                "is_trial": subscription.is_trial,
                "auto_renew": subscription.auto_renew,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "stripe_customer_id": subscription.stripe_customer_id,
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "plan": {
                    "id": subscription.plan.id,
                    "name": subscription.plan.name,
                    "price": float(subscription.plan.price),
                    "discount": float(subscription.plan.discount),
                    "final_price": float(subscription.plan.final_price),
                    "duration": subscription.plan.duration,
                    "is_active": subscription.plan.is_active,
                }
            }

        # -------------------------
        # Profiles
        # -------------------------
        business_profile = BusinessProfile.objects.filter(user=user).first()
        landscaper_basic = LandscaperProfilies.objects.filter(user=user).first()

        business_profile_data = None
        if business_profile:
            business_profile_data = {
                "id": business_profile.id,
                "business_name": getattr(business_profile, "business_name", None),
                "bio": getattr(business_profile, "bio", None),  # SAFE
                "selected_location": getattr(business_profile, "selected_location", None),
                "address": getattr(user, "address", None),

                # ✅ real name
                "real_name": (
                    getattr(landscaper_basic, "name", None)
                    if landscaper_basic else getattr(user, "name", None)
                )
            }

        # -------------------------
        # Login Activity
        # -------------------------
        login_qs = LoginActivity.objects.filter(user=user).order_by("-created_at")[:20]

        login_activity = [{
            "id": x.id,
            "ip_address": x.ip_address,
            "device_type": x.device_type,
            "os": x.os,
            "browser": x.browser,
            "user_agent": x.user_agent,
            "created_at": x.created_at,
        } for x in login_qs]

        # -------------------------
        # DEFAULT METRICS
        # -------------------------
        total_revenue = 0.0
        total_jobs = 0
        completed_jobs = 0
        pending_jobs = 0
        total_clients = 0
        total_connected_clients = 0
        total_reviews = 0
        average_rating = 0.0
        recent_jobs = []

        # -------------------------
        # JOB METRICS
        # -------------------------
        if business_profile:
            jobs_qs = Job.objects.filter(landscaper=business_profile)

            total_jobs = jobs_qs.count()

            completed_jobs = jobs_qs.filter(
                status=Job.Status.COMPLETED
            ).count()

            pending_jobs = jobs_qs.exclude(
                status=Job.Status.COMPLETED
            ).count()

            total_clients = jobs_qs.values("client_id").distinct().count()
            total_connected_clients = total_clients

            total_revenue = jobs_qs.filter(
                payment_status=Job.PaymentStatus.PAID
            ).aggregate(
                total=Coalesce(Sum("total_price"), Value(0.0), output_field=FloatField())
            )["total"] or 0.0

            # -------------------------
            # REVIEWS
            # -------------------------
            reviews_qs = LandscaperReview.objects.filter(landscaper=user)

            total_reviews = reviews_qs.count()

            average_rating = reviews_qs.aggregate(
                avg=Coalesce(Avg("rating"), Value(0.0))
            )["avg"] or 0.0

            # -------------------------
            # RECENT JOBS
            # -------------------------
            recent_jobs_qs = (
                jobs_qs.select_related("client")
                .order_by("-created_at")[:10]
            )

            for job in recent_jobs_qs:
                client_user = getattr(job.client, "user", None)

                recent_jobs.append({
                    "id": job.id,
                    "service_name": f"Job #{job.id}",  # fallback

                    "scheduled_date": job.scheduled_date,
                    "scheduled_time": job.scheduled_time,

                    "is_completed": job.status == Job.Status.COMPLETED,

                    "completed_at": job.completed_at,
                    "payment_status": job.payment_status,

                    "client_profile_id": job.client_id,
                    "client_id": client_user.id if client_user else None,
                    "client_name": job.client_name,
                    "client_email": job.client_email,
                })

        # -------------------------
        # Audit Logs
        # -------------------------
        recent_logs_qs = (
            AdminAuditLog.objects
            .filter(target_user=user)
            .select_related("admin")
            .order_by("-created_at")[:10]
        )

        recent_audit_logs = [{
            "id": log.id,
            "admin_id": log.admin.id,
            "admin_email": log.admin.email,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at,
        } for log in recent_logs_qs]

        # -------------------------
        # FINAL RESPONSE (UNCHANGED)
        # -------------------------
        payload = {
            **AdminUserDetailSerializer(user).data,
            "subscription": subscription_data,
            "business_profile": business_profile_data,
            "total_revenue": float(total_revenue),
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "pending_jobs": pending_jobs,
            "total_clients": total_clients,
            "total_connected_clients": total_connected_clients,
            "total_reviews": total_reviews,
            "average_rating": round(float(average_rating), 2),
            "recent_jobs": recent_jobs,
            "recent_audit_logs": recent_audit_logs,
            "login_activity": login_activity,
        }

        return Response(payload, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data.get("action")
        admin_notes = serializer.validated_data.get("admin_notes")
        role = serializer.validated_data.get("role")

        changes = []

        if action == "pause":
            user.is_active = False
            changes.append("paused user")
        elif action == "unpause":
            user.is_active = True
            changes.append("unpaused user")
        elif action == "flag":
            user.is_flagged = True
            changes.append("flagged user")
        elif action == "unflag":
            user.is_flagged = False
            changes.append("unflagged user")

        if admin_notes is not None:
            user.admin_notes = admin_notes
            changes.append("updated admin notes")

        if role:
            old_role = user.role
            user.role = role
            changes.append(f"changed role from {old_role} to {role}")

        user.save()

        if changes:
            AdminAuditLog.objects.create(
                admin=request.user,
                action="Admin updated user",
                target_user=user,
                details="; ".join(changes)
            )

        return Response({
            "status": "success",
            "message": "User updated successfully",
            "changes": changes
        }, status=status.HTTP_200_OK)




# accounts/admin_security_views.py
class AdminLoginActivityListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        user_id = request.query_params.get("user_id")  # optional filter

        qs = LoginActivity.objects.select_related("user").all()

        if user_id:
            qs = qs.filter(user_id=user_id)

        qs = qs.order_by("-created_at")[:200]  # limit for performance

        data = []
        for x in qs:
            data.append({
                "id": x.id,
                "user_id": x.user.id,
                "email": x.user.email,
                "ip_address": x.ip_address,
                "device_type": x.device_type,
                "os": x.os,
                "browser": x.browser,
                "user_agent": x.user_agent,
                "created_at": x.created_at,
            })

        return Response({"count": len(data), "data": data})


class AdminUserLoginActivityView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        qs = LoginActivity.objects.filter(user=user).order_by("-created_at")[:50]

        data = [{
            "id": x.id,
            "ip_address": x.ip_address,
            "device_type": x.device_type,
            "os": x.os,
            "browser": x.browser,
            "user_agent": x.user_agent,
            "created_at": x.created_at,
        } for x in qs]

        return Response({
            "user_id": user.id,
            "email": user.email,
            "last_login": user.last_login,
            "logins": data
        })

# user list
# subscriptions/admin_views.py

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from subscriptions.models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


class AdminSubscriptionBillingHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id, role="landscaper")

        subscription = (
            Subscription.objects
            .select_related("plan")
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

        if not subscription:
            return Response({
                "status": "success",
                "user_id": user.id,
                "user_email": user.email,
                "billing_history": []
            }, status=status.HTTP_200_OK)

        if not subscription.stripe_customer_id or not subscription.stripe_subscription_id:
            # fallback: local subscription snapshot only
            return Response({
                "status": "success",
                "user_id": user.id,
                "user_email": user.email,
                "billing_history": [
                    {
                        "date": subscription.created_at,
                        "plan_type": subscription.plan.name,
                        "plan_price": float(subscription.plan.price),
                        "status": subscription.status,
                        "invoice_id": None,
                        "invoice_number": None,
                        "invoice_pdf": None,
                        "hosted_invoice_url": None,
                    }
                ]
            }, status=status.HTTP_200_OK)

        try:
            invoices = stripe.Invoice.list(
                customer=subscription.stripe_customer_id,
                subscription=subscription.stripe_subscription_id,
                limit=100
            )
        except Exception as e:
            return Response(
                {"detail": f"Stripe invoice fetch failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        billing_history = []

        for inv in invoices.auto_paging_iter():
            line_plan_name = None
            line_plan_price = None

            if inv.get("lines") and inv["lines"].get("data"):
                first_line = inv["lines"]["data"][0]
                pricing = first_line.get("pricing", {})
                price_details = pricing.get("price_details", {})
                line_plan_name = first_line.get("description") or subscription.plan.name
                line_plan_price = (
                    inv.get("amount_paid", 0) / 100.0
                    if inv.get("amount_paid") is not None
                    else float(subscription.plan.price)
                )

            billing_history.append({
                "invoice_id": inv.get("id"),
                "invoice_number": inv.get("number"),
                "date": inv.get("created"),
                "period_start": inv.get("period_start"),
                "period_end": inv.get("period_end"),
                "plan_type": line_plan_name or subscription.plan.name,
                "plan_price": line_plan_price if line_plan_price is not None else float(subscription.plan.price),
                "amount_paid": (inv.get("amount_paid", 0) / 100.0),
                "amount_due": (inv.get("amount_due", 0) / 100.0),
                "currency": inv.get("currency"),
                "status": inv.get("status"),
                "billing_reason": inv.get("billing_reason"),
                "hosted_invoice_url": inv.get("hosted_invoice_url"),
                "invoice_pdf": inv.get("invoice_pdf"),
            })

        return Response({
            "status": "success",
            "user_id": user.id,
            "user_email": user.email,
            "subscription_id": subscription.id,
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "billing_history": billing_history
        }, status=status.HTTP_200_OK)


class AdminSubscriptionInvoiceDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id, invoice_id):
        user = get_object_or_404(User, id=user_id, role="landscaper")

        subscription = (
            Subscription.objects
            .select_related("plan")
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

        if not subscription or not subscription.stripe_customer_id:
            return Response(
                {"detail": "No Stripe subscription found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
        except Exception as e:
            return Response(
                {"detail": f"Stripe invoice fetch failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if invoice.get("customer") != subscription.stripe_customer_id:
            return Response(
                {"detail": "Invoice does not belong to this user."},
                status=status.HTTP_403_FORBIDDEN
            )

        invoice_lines = []
        for line in invoice.get("lines", {}).get("data", []):
            invoice_lines.append({
                "description": line.get("description"),
                "amount": (line.get("amount", 0) / 100.0),
                "currency": line.get("currency"),
                "period_start": line.get("period", {}).get("start"),
                "period_end": line.get("period", {}).get("end"),
            })

        return Response({
            "status": "success",
            "user_id": user.id,
            "user_email": user.email,
            "invoice": {
                "invoice_id": invoice.get("id"),
                "invoice_number": invoice.get("number"),
                "date": invoice.get("created"),
                "customer": invoice.get("customer"),
                "subscription": invoice.get("subscription"),
                "status": invoice.get("status"),
                "currency": invoice.get("currency"),
                "amount_paid": (invoice.get("amount_paid", 0) / 100.0),
                "amount_due": (invoice.get("amount_due", 0) / 100.0),
                "subtotal": (invoice.get("subtotal", 0) / 100.0),
                "total": (invoice.get("total", 0) / 100.0),
                "billing_reason": invoice.get("billing_reason"),
                "hosted_invoice_url": invoice.get("hosted_invoice_url"),
                "invoice_pdf": invoice.get("invoice_pdf"),
                "lines": invoice_lines
            }
        }, status=status.HTTP_200_OK)