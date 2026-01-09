from django.urls import path, include
from .views import (
    SignupView, 
    LoginView, 
    SendOTPView, 
    VerifyOTPView, 
    ResetPasswordView, 
    UserListView,
    AdminDeleteUserView,
    VerifyOTPForgetView,
    ResendOTPView,
    ResendForgotOTPView
    
)

urlpatterns = [
    # Your custom authentication views
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('resend-email/', ResendOTPView.as_view(), name='resend-otp'),
    path('verify-email/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendForgotOTPView.as_view(), name='resend-forgot-otp'),
    path('verify-otp/', VerifyOTPForgetView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    # path('admin/create/', AdminCreateView.as_view(), name='admin-create'),
    # path('check/token/', CheckTokenView.as_view(), name='check-token'),
    path('users-list/', UserListView.as_view(), name='user-list'),
    path("admin/delete-user/<int:id>/", AdminDeleteUserView.as_view(), name="admin-delete-user"),

]