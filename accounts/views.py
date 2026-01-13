from django.shortcuts import render

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
from .models import User, OTP
from django.utils import timezone
from .utils import generate_otp, send_otp_email 
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer,VerifyOTPForgetSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken



# signup views 
class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data["email"]

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User with this email already exists."},
                status=400
            )

        # ✅ STORE SESSION
        request.session["pending_user"] = {
            "email": email,
            "name": data["name"],
            "password": data["password"],
            "phone": data.get("phone"),
            "address": data.get("address"),
            "role": data["role"],
        }
        request.session.modified = True

        # ✅ EMAIL-BASED OTP
        OTP.objects.filter(email=email).delete()

        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        send_otp_email(email, otp_code, data["name"])

        return Response(
            {"detail": "Verification OTP sent to email."},
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


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        print("user", user)

        # ---------------------------------------------------------
        # 🔥 CHANGE ADDED HERE → Check if user is NOT verified
        # ---------------------------------------------------------
        if not user.is_active:
            return Response(
                {"message": "Please verify your email first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------
        # 🔥 Login allowed only if email is verified
        # ---------------------------------------------------------
        tokens = get_tokens_for_user(user)
        print("tokens", tokens)

        return Response({
            "message": "Login successful",
            "token": tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "phone": getattr(user, 'phone', None),      
                "address": getattr(user, 'address', None),  
            }
        }, status=status.HTTP_200_OK)




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
#         otp_code = request.data.get("otp")

#         if not email or not otp_code:
#             return Response(
#                 {"detail": "Email and OTP are required."},
#                 status=400
#             )

#         try:
#             otp_instance = OTP.objects.filter(
#                 email=email,
#                 code=otp_code
                
#             ).latest("created_at")
#             # print(email,code)
#         except OTP.DoesNotExist:
#             return Response(
#                 {"detail": "OTP not found."},
#                 status=400
#             )

#         if otp_instance.is_expired():
#             otp_instance.delete()
#             return Response(
#                 {"detail": "OTP expired."},
#                 status=400
#             )

#         pending = request.session.get("pending_user")
#         print("pending", pending)
#         if not pending or pending["email"] != email:
#             return Response(
#                 {"detail": "Signup data missing. Restart signup."},
#                 status=400
#             )

#         # ✅ CREATE USER
#         User.objects.create_user(
#             email=pending["email"],
#             name=pending["name"],
#             password=pending["password"],
#             phone=pending["phone"],
#             address=pending["address"],
#             role=pending["role"],
#             is_active=True
#         )

#         # Cleanup
#         otp_instance.delete()
#         del request.session["pending_user"]

#         return Response(
#             {"message": "Email verified and account created successfully."},
#             status=200
#         )


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

        # ✅ CREATE USER
        user = User.objects.create_user(
            email=pending_user["email"],
            name=pending_user["name"],
            password=pending_user["password"],
            phone=pending_user.get("phone"),
            address=pending_user.get("address"),
            role="user"   
        )


        # cleanup
        OTP.objects.filter(email=email).delete()
        request.session.flush()

        # ✅ GENERATE TOKENS (CORRECT PLACE)
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
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

class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        role = request.query_params.get("role")
        plan = request.query_params.get("plan")  # basic | pro
        status_param = request.query_params.get("status")  # active | paused
        search_query = request.query_params.get("search", "").strip()

        users = User.objects.all()

        # Filter by role
        if role:
            users = users.filter(role=role)

        # Filter by subscription plan
        if plan:
            users = users.filter(
                subscription__is_active=True,
                subscription__plan__name__iexact=plan
            )

        # Filter by active/paused
        if status_param:
            if status_param.lower() == "paused":
                users = users.filter(is_active=False)
            elif status_param.lower() == "active":
                users = users.filter(is_active=True)

        # Search by name or email
        if search_query:
            users = users.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        users = users.distinct()

        # 📊 Stats
        total_users = User.objects.count()
        total_clients = User.objects.filter(role="client").count()
        total_landscapers = User.objects.filter(role="landscaper").count()

        total_basic_landscapers = User.objects.filter(
            role="landscaper",
            subscription__is_active=True,
            subscription__plan__name__iexact="basic"
        ).distinct().count()

        total_pro_landscapers = User.objects.filter(
            role="landscaper",
            subscription__is_active=True,
            subscription__plan__name__iexact="pro"
        ).distinct().count()

        paused_users = User.objects.filter(is_active=False).count()
        active_users = User.objects.filter(is_active=True).count()

        last_24h = timezone.now() - timedelta(hours=24)
        daily_active_users = User.objects.filter(
            last_login__gte=last_24h
        ).count()

        serializer = UserSerializer(users, many=True)

        return Response({
            "status": "success",
            "summary": {
                "total_users": total_users,
                "total_clients": total_clients,
                "total_landscapers": total_landscapers,
                "basic_landscapers": total_basic_landscapers,
                "pro_landscapers": total_pro_landscapers,
                "paused_users": paused_users,
                "active_users": active_users,
                "daily_active_users": daily_active_users,
            },
            "data": serializer.data,
        }, status=200)





# delete user for admin views 
class AdminDeleteUserView(generics.DestroyAPIView):
    """
    Admin can delete any user by ID safely.
    Only superusers can delete other superusers.
    """
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        user_to_delete = self.get_object()

        # Only superuser can delete another superuser
        if user_to_delete.is_superuser and not request.user.is_superuser:
            return Response(
                {"detail": "Only a superuser can delete another superuser."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Delete the user
        email = user_to_delete.email
        user_to_delete.delete()

        return Response(
            {"detail": f"User {email} deleted successfully."},
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
