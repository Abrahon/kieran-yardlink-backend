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
    ResendForgotOTPView,
    AdminPauseUserView,
    SelfDeleteUserView,
    ReportUserAPIView,
    AdminAuditLogView,
    AdminVerifyOTPView,
    AdminUserDetailView,
    AdminLoginActivityListView,
    AdminUserLoginActivityView,
    AdminSubscriptionBillingHistoryView,
    AdminSubscriptionInvoiceDetailView,
    AdminUserSuspendView

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
    path('admin/users/<int:user_id>/pause/', AdminPauseUserView.as_view(), name='admin-pause-user'),
    path("users/me/delete/", SelfDeleteUserView.as_view(), name="self-delete-user"),
    path("report/<int:user_id>/", ReportUserAPIView.as_view(), name="report-user"),
    path("admin/verify-otp/", AdminVerifyOTPView.as_view(), name="admin-verify-otp"),
    # audit log
    path("admin/audit-logs/", AdminAuditLogView.as_view(), name="admin-audit-logs"),
    # user details
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    # login activities
    path("admin/login-activities/", AdminLoginActivityListView.as_view(), name="admin-login-activities"),
    path("admin/users/<int:user_id>/login-activities/", AdminUserLoginActivityView.as_view(), name="admin-user-login-activities"),
 
    # subscriptions/urls.py
    path("admin/users/<int:user_id>/subscription-billing-history/",AdminSubscriptionBillingHistoryView.as_view(),name="admin-subscription-billing-history"),
    path("admin/users/<int:user_id>/subscription-invoices/<str:invoice_id>/",AdminSubscriptionInvoiceDetailView.as_view(),name="admin-subscription-invoice-detail"),
    path("admin/users/<int:user_id>/suspend/", AdminUserSuspendView.as_view(), name="admin-user-suspend"),

]