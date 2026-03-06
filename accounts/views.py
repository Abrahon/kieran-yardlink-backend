from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
# Create your views here.
from urllib.parse import urlencode, unquote
from .serializers import UserSerializer
import requests
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


from accounts.models import LoginActivity

from django.db.models import Q, Sum, FloatField, Count

from subscriptions.models import Subscription, SubscriptionStatus
from services.models import ServiceSchedule, PaymentStatus
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

# class LoginView(generics.GenericAPIView):
#     serializer_class = LoginSerializer
#     permission_classes = [AllowAny]
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         print("user", user)

#         # ---------------------------------------------------------
#         #  CHANGE ADDED HERE → Check if user is NOT verified
#         # ---------------------------------------------------------
#         if not user.is_active:
#             return Response(
#                 {"message": "Please verify your email first."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # ---------------------------------------------------------
#         #  Login allowed only if email is verified
#         # ---------------------------------------------------------
#         tokens = get_tokens_for_user(user)
#         print("tokens", tokens)

#         return Response({
#             "message": "Login successful",
#             "token": tokens,
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "name": user.name,
#                 "role": user.role,
#                 "phone": getattr(user, 'phone', None),      
#                 "address": getattr(user, 'address', None), 
#                 # ✅ Add latitude & longitude
#                 "latitude": float(user.latitude) if getattr(user, "latitude", None) else None,
#                 "longitude": float(user.longitude) if getattr(user, "longitude", None) else None, 
#             }
#         }, status=status.HTTP_200_OK)


# class LoginView(generics.GenericAPIView):
#     serializer_class = LoginSerializer
#     permission_classes = [AllowAny]
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = serializer.validated_data['user']

#         if not user.is_active:
#             return Response(
#                 {"message": "Please verify your email first."},
#                 status=400
#             )

#         # 🔐 STEP 1 → If ADMIN → send OTP
#         if user.role == "admin":

#             OTP.objects.filter(user=user).delete()

#             otp_code = generate_otp()

#             OTP.objects.create(
#                 user=user,
#                 code=otp_code
#             )

#             send_otp_email(user.email, otp_code)

#             return Response({
#                 "message": "OTP sent to admin email",
#                 "admin_2fa_required": True,
#                 "email": user.email
#             })

#         # Normal users login directly
#         tokens = get_tokens_for_user(user)

#         return Response({
#             "message": "Login successful",
#             "token": tokens,
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "name": user.name,
#                 "role": user.role,
#                 "phone": getattr(user, 'phone', None),      
#                 "address": getattr(user, 'address', None), 
#                 # ✅ Add latitude & longitude
#                 "latitude": float(user.latitude) if getattr(user, "latitude", None) else None,
#                 "longitude": float(user.longitude) if getattr(user, "longitude", None) else None, 
#             }
#         }, status=status.HTTP_200_OK)

from .serializers import LoginSerializer
from .models import User, OTP, LoginActivity
from .utils import generate_otp, send_otp_email
from .security_utils import get_client_ip, parse_device

# your existing function
from .views import get_tokens_for_user  # adjust import if it's in same file remove this


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
        ip = get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")

        device_info = parse_device(ua)

        LoginActivity.objects.create(
            user=user,
            ip_address=ip,
            user_agent=ua,
            device_type=device_info.get("device_type"),
            os=device_info.get("os"),
            browser=device_info.get("browser"),
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

# class VerifyOTPView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         email = request.data.get("email")
#         otp = request.data.get("otp")

#         otp_obj = OTP.objects.filter(email=email, code=otp).first()
#         if not otp_obj:
#             return Response(
#                 {"detail": "Invalid or expired OTP"},
#                 status=400
#             )

#         pending_user = request.session.get("pending_user")
#         if not pending_user or pending_user["email"] != email:
#             return Response(
#                 {"detail": "Session expired. Please signup again."},
#                 status=400
#             )

#         # ✅ CREATE USER with correct role from session
#         user = User.objects.create_user(
#             email=pending_user["email"],
#             name=pending_user["name"],
#             password=pending_user["password"],
#             phone=pending_user.get("phone"),
#             address=pending_user.get("address"),
#             role=pending_user["role"]   # <-- fixed
#         )

#         # cleanup
#         OTP.objects.filter(email=email).delete()
#         request.session.flush()

#         # ✅ GENERATE TOKENS
#         refresh = RefreshToken.for_user(user)

#         return Response({
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "role": user.role   # now correctly shows "client", "landscaper", etc.
#             }
#         }, status=201)
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


# userlist views

# class UserListView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):
#         role = request.query_params.get("role")
#         plan = request.query_params.get("plan")  # basic | pro
#         status_param = request.query_params.get("status")  # active | paused
#         search_query = request.query_params.get("search", "").strip()

#         users = User.objects.all()

#         # --------------------------
#         # Filters
#         # --------------------------
#         if role:
#             users = users.filter(role=role)
#         if plan:
#             users = users.filter(
#                 subscription__is_active=True,
#                 subscription__plan__name__iexact=plan
#             )
#         if status_param:
#             if status_param.lower() == "paused":
#                 users = users.filter(is_active=False)
#             elif status_param.lower() == "active":
#                 users = users.filter(is_active=True)
#         if search_query:
#             users = users.filter(
#                 Q(name__icontains=search_query) |
#                 Q(email__icontains=search_query)
#             )
#         users = users.distinct()

#         # --------------------------
#         # Basic stats
#         # --------------------------
#         total_users = User.objects.count()
#         total_clients = User.objects.filter(role="client").count()
#         total_landscapers = User.objects.filter(role="landscaper").count()
#         total_basic_landscapers = User.objects.filter(
#             role="landscaper",
#             subscription__is_active=True,
#             subscription__plan__name__iexact="basic"
#         ).distinct().count()
#         total_pro_landscapers = User.objects.filter(
#             role="landscaper",
#             subscription__is_active=True,
#             subscription__plan__name__iexact="pro"
#         ).distinct().count()
#         paused_users = User.objects.filter(is_active=False).count()
#         active_users = User.objects.filter(is_active=True).count()
#         last_24h = timezone.now() - timedelta(hours=24)
#         daily_active_users = User.objects.filter(last_login__gte=last_24h).count()

#         # --------------------------
#         # Active / Inactive ratio
#         # --------------------------
#         if total_users > 0:
#             active_ratio = round((active_users / total_users) * 100, 2)
#             inactive_ratio = round((paused_users / total_users) * 100, 2)
#         else:
#             active_ratio = inactive_ratio = 0

#         # --------------------------
#         # Daily average users
#         # --------------------------
#         first_user = User.objects.order_by("date_joined").first()
#         if first_user:
#             days_active = max((timezone.now() - first_user.date_joined).days, 1)
#             daily_average_users = round(total_users / days_active, 2)
#         else:
#             daily_average_users = 0

#         # --------------------------
#         # New signups weekly & total
#         # --------------------------
#         one_week_ago = timezone.now() - timedelta(days=7)
#         weekly_new_users = User.objects.filter(date_joined__gte=one_week_ago).count()
#         total_new_users = total_users

#         # --------------------------
#         # Active subscriptions & jobs
#         # --------------------------
#         active_subscriptions_count = Subscription.objects.filter(
#             user__in=users, status=SubscriptionStatus.ACTIVE
#         ).count()
#         active_jobs_count = ServiceSchedule.objects.filter(
#             is_completed=False, landscaper__user__in=users
#         ).count()

#         # --------------------------
#         # Platform fees (2% from paid jobs)
#         # --------------------------
#         paid_jobs = ServiceSchedule.objects.filter(payment_status=PaymentStatus.PAID)
#         total_job_amount = paid_jobs.aggregate(
#             total=Sum('service__price', output_field=FloatField())
#         )['total'] or 0.0
#         job_platform_fee = round(total_job_amount * 0.02, 2)

#         # --------------------------
#         # Serialize users
#         # --------------------------
#         serializer = UserSerializer(users, many=True, context={"request": request})

#         return Response({
#             "status": "success",
#             "summary": {
#                 "total_users": total_users,
#                 "total_clients": total_clients,
#                 "total_landscapers": total_landscapers,
#                 "basic_landscapers": total_basic_landscapers,
#                 "pro_landscapers": total_pro_landscapers,
#                 "paused_users": paused_users,
#                 "active_users": active_users,
#                 "active_ratio": active_ratio,
#                 "inactive_ratio": inactive_ratio,
#                 "daily_active_users": daily_active_users,
#                 "daily_average_users": daily_average_users,
#                 "weekly_new_signups": weekly_new_users,
#                 "total_new_signups": total_new_users,
#                 "active_subscriptions": active_subscriptions_count,
#                 "active_jobs": active_jobs_count,
#                 "platform_fee_collected": job_platform_fee
#             },
#             "data": serializer.data,
#         }, status=200)

# from django.db.models import (
#     Q,
#     Count,
#     Sum,
#     Avg,
#     FloatField
# )
# from django.utils import timezone
# from datetime import timedelta

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAdminUser
# from rest_framework.response import Response
# from rest_framework.pagination import PageNumberPagination

# class UserListView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):

#         role = request.query_params.get("role")
#         plan = request.query_params.get("plan")
#         status_param = request.query_params.get("status")
#         location = request.query_params.get("location")
#         search_query = request.query_params.get("search", "").strip()
#         sort_by = request.query_params.get("sort")

#         users = User.objects.all()

#         # --------------------------------
#         # FILTERS
#         # --------------------------------

#         if role:
#             users = users.filter(role__iexact=role)

#         if plan:
#             users = users.filter(
#                 subscription__is_active=True,
#                 subscription__plan__name__iexact=plan
#             )

#         if status_param:
#             if status_param.lower() == "paused":
#                 users = users.filter(is_active=False)
#             elif status_param.lower() == "active":
#                 users = users.filter(is_active=True)

#         if location:
#             users = users.filter(address__icontains=location)

#         # --------------------------------
#         # GLOBAL SEARCH
#         # --------------------------------

#         if search_query:
#             users = users.filter(
#                 Q(name__icontains=search_query) |
#                 Q(email__icontains=search_query) |
#                 Q(role__icontains=search_query) |
#                 Q(address__icontains=search_query) |
#                 Q(subscription__plan__name__icontains=search_query) |
#                 Q(subscription__status__icontains=search_query)
#             )

#         # --------------------------------
#         # ANNOTATIONS (metrics)
#         # --------------------------------

#         users = users.annotate(

#             total_clients=Count(
#                 "landscaper_jobs__client",
#                 distinct=True
#             ),

#             total_jobs=Count(
#                 "landscaper_jobs",
#                 distinct=True
#             ),

#             total_revenue=Sum(
#                 "landscaper_jobs__service__price",
#                 output_field=FloatField()
#             ),

#             average_rating=Avg(
#                 "reviews__rating"
#             )
#         )

#         # --------------------------------
#         # SORTING
#         # --------------------------------

#         if sort_by == "revenue":
#             users = users.order_by("-total_revenue")

#         elif sort_by == "clients":
#             users = users.order_by("-total_clients")

#         elif sort_by == "rating":
#             users = users.order_by("-average_rating")

#         elif sort_by == "jobs":
#             users = users.order_by("-total_jobs")

#         elif sort_by == "newest":
#             users = users.order_by("-date_joined")

#         users = users.distinct()

#         # --------------------------------
#         # PAGINATION
#         # --------------------------------

#         paginator = PageNumberPagination()
#         paginator.page_size = 20

#         page = paginator.paginate_queryset(users, request)

#         serializer = UserSerializer(
#             page,
#             many=True,
#             context={"request": request}
#         )

#         # --------------------------------
#         # DASHBOARD SUMMARY
#         # --------------------------------

#         total_users = User.objects.count()

#         total_clients = User.objects.filter(
#             role="client"
#         ).count()

#         total_landscapers = User.objects.filter(
#             role="landscaper"
#         ).count()

#         paused_users = User.objects.filter(
#             is_active=False
#         ).count()

#         active_users = User.objects.filter(
#             is_active=True
#         ).count()

#         last_24h = timezone.now() - timedelta(hours=24)

#         daily_active_users = User.objects.filter(
#             last_login__gte=last_24h
#         ).count()

#         # Weekly new signups
#         one_week_ago = timezone.now() - timedelta(days=7)

#         weekly_new_users = User.objects.filter(
#             date_joined__gte=one_week_ago
#         ).count()

#         # Platform fees from jobs
#         paid_jobs = ServiceSchedule.objects.filter(
#             payment_status=PaymentStatus.PAID
#         )

#         total_job_amount = paid_jobs.aggregate(
#             total=Sum("service__price", output_field=FloatField())
#         )["total"] or 0.0

#         platform_fee = round(total_job_amount * 0.02, 2)

#         return paginator.get_paginated_response({

#             "summary": {

#                 "total_users": total_users,
#                 "total_clients": total_clients,
#                 "total_landscapers": total_landscapers,
#                 "active_users": active_users,
#                 "paused_users": paused_users,
#                 "daily_active_users": daily_active_users,
#                 "weekly_new_signups": weekly_new_users,
#                 "platform_fee_collected": platform_fee
#             },

#             "data": serializer.data
#         })

from datetime import timedelta
from django.db.models import (
    Q, Count, Sum, FloatField, Value, OuterRef, Subquery
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from accounts.models import User
from accounts.serializers import UserSerializer
from subscriptions.models import Subscription, SubscriptionStatus
from services.models import ServiceSchedule, PaymentStatus
from landscapers.models import BusinessProfile   # adjust import if needed


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
        # GLOBAL SEARCH
        # --------------------------

        if search_query:
            users = users.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(role__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(subscription__plan__name__icontains=search_query) |
                Q(subscription__status__icontains=search_query)
            )

        users = users.distinct()

        # ==========================================================
        # Subqueries using BusinessProfile
        # ==========================================================

        business_profile_sq = BusinessProfile.objects.filter(
            user=OuterRef("pk")
        ).values("id")[:1]

        revenue_sq = ServiceSchedule.objects.filter(
            landscaper_id=Subquery(business_profile_sq),
            payment_status=PaymentStatus.PAID
        ).values("landscaper_id").annotate(
            total=Sum("service__price", output_field=FloatField())
        ).values("total")[:1]

        jobs_sq = ServiceSchedule.objects.filter(
            landscaper_id=Subquery(business_profile_sq)
        ).values("landscaper_id").annotate(
            total=Count("id")
        ).values("total")[:1]

        completed_jobs_sq = ServiceSchedule.objects.filter(
            landscaper_id=Subquery(business_profile_sq),
            is_completed=True
        ).values("landscaper_id").annotate(
            total=Count("id")
        ).values("total")[:1]

        clients_sq = ServiceSchedule.objects.filter(
            landscaper_id=Subquery(business_profile_sq)
        ).values("landscaper_id").annotate(
            total=Count("client_id", distinct=True)
        ).values("total")[:1]

        users = users.annotate(
            total_revenue=Coalesce(Subquery(revenue_sq, output_field=FloatField()), Value(0.0)),
            total_jobs=Coalesce(Subquery(jobs_sq), Value(0)),
            completed_jobs=Coalesce(Subquery(completed_jobs_sq), Value(0)),
            total_clients=Coalesce(Subquery(clients_sq), Value(0)),
        )

        # --------------------------
        # SORTING
        # --------------------------

        if sort_by == "revenue":
            users = users.order_by("-total_revenue", "-date_joined")

        elif sort_by == "clients":
            users = users.order_by("-total_clients", "-date_joined")

        elif sort_by == "jobs":
            users = users.order_by("-total_jobs", "-date_joined")

        elif sort_by == "newest":
            users = users.order_by("-date_joined")

        else:
            users = users.order_by("-date_joined")

        # --------------------------
        # SUMMARY
        # --------------------------

        total_users = User.objects.count()

        total_clients = User.objects.filter(
            role="client"
        ).count()

        total_landscapers = User.objects.filter(
            role="landscaper"
        ).count()

        paused_users = User.objects.filter(
            is_active=False
        ).count()

        active_users = User.objects.filter(
            is_active=True
        ).count()

        last_24h = timezone.now() - timedelta(hours=24)

        daily_active_users = User.objects.filter(
            last_login__gte=last_24h
        ).count()

        one_week_ago = timezone.now() - timedelta(days=7)

        weekly_new_signups = User.objects.filter(
            date_joined__gte=one_week_ago
        ).count()

        paid_jobs = ServiceSchedule.objects.filter(
            payment_status=PaymentStatus.PAID
        )

        total_job_amount = paid_jobs.aggregate(
            total=Sum("service__price", output_field=FloatField())
        )["total"] or 0.0

        platform_fee_collected = round(total_job_amount * 0.02, 2)

        active_subscriptions = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE
        ).count()

        # --------------------------
        # PAGINATION
        # --------------------------

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(users, request)

        serializer = UserSerializer(page, many=True, context={"request": request})

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
                "platform_fee_collected": platform_fee_collected
            },

            "data": serializer.data
        })

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

class AdminPauseUserView(APIView):
    """
    Admin API to pause (deactivate) or unpause (activate) a user
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        """
        Toggle user's active status.
        Send JSON payload: {"action": "pause"} or {"action": "unpause"}
        """
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
        
        # 🔐 Create audit log
        AdminAuditLog.objects.create(
            admin=request.user,
            action=log_action,
            target_user=user,
            details=f"Admin {request.user.email} performed '{log_action}' on {user.email}"
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



from django.shortcuts import get_object_or_404
from django.db.models import Sum, FloatField, Value
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import User, AdminAuditLog
from .serializers import AdminUserDetailSerializer, AdminUserUpdateSerializer

from subscriptions.models import Subscription
from services.models import ServiceSchedule, PaymentStatus

# ✅ BusinessProfile stays where it is (your landscapers app)
from landscapers.models import BusinessProfile

# ✅ LandscaperProfilies is in profiles app (as you said)
from profiles.models import LandscaperProfilies


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # -------------------------
        # Subscription info
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
        # Business Profile info (business details)
        # -------------------------
        business_profile = BusinessProfile.objects.filter(user=user).first()
        business_profile_data = None

        if business_profile:
            business_profile_data = {
                "id": business_profile.id,
                "business_name": getattr(business_profile, "business_name", None),
                "bio": getattr(business_profile, "bio", None),
                "selected_location": getattr(business_profile, "selected_location", None),
                "address": user.address,
            }
        
        from accounts.models import LoginActivity  # add at top


        # -------------------------
        # Recent login activities
        # -------------------------
        login_qs = (
            LoginActivity.objects
            .filter(user=user)
            .order_by("-created_at")[:20]
        )

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
        # Landscaper Profile info (jobs metrics)
        # -------------------------
        landscaper_profile = LandscaperProfilies.objects.filter(user=user).first()

        total_revenue = 0.0
        total_jobs = 0
        completed_jobs = 0
        pending_jobs = 0
        total_clients = 0
        recent_jobs = []

        if landscaper_profile:
            # ✅ FIX: filter by LandscaperProfilies instance
            jobs_qs = ServiceSchedule.objects.filter(landscaper=landscaper_profile)

            total_jobs = jobs_qs.count()
            completed_jobs = jobs_qs.filter(is_completed=True).count()
            pending_jobs = jobs_qs.filter(is_completed=False).count()
            total_clients = jobs_qs.values("client_id").distinct().count()

            total_revenue = jobs_qs.filter(
                payment_status=PaymentStatus.PAID
            ).aggregate(
                total=Coalesce(Sum("service__price", output_field=FloatField()), Value(0.0))
            )["total"] or 0.0

            recent_jobs_qs = (
                jobs_qs.select_related("service", "client")
                .order_by("-created_at")[:10]
            )

            for job in recent_jobs_qs:
                client_user = getattr(job.client, "user", None)
                recent_jobs.append({
                    "id": job.id,
                    "service_name": getattr(job.service, "name", None),
                    "service_price": float(getattr(job.service, "price", 0) or 0),
                    "scheduled_date": job.scheduled_date,
                    "scheduled_time": job.scheduled_time,
                    "is_completed": job.is_completed,
                    "completed_at": job.completed_at,
                    "payment_status": job.payment_status,
                    "stripe_payment_id": job.stripe_payment_id,
                    "client_profile_id": job.client_id,
                    "client_id": client_user.id if client_user else None,
                    "client_name": client_user.name if client_user else None,
                    "client_email": client_user.email if client_user else None,
                    
                })

        # -------------------------
        # Recent audit logs
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

        payload = {
            **AdminUserDetailSerializer(user).data,
            "subscription": subscription_data,
            "business_profile": business_profile_data,
            "total_revenue": float(total_revenue),
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "pending_jobs": pending_jobs,
            "total_clients": total_clients,
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


# login activities 
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

