from django.urls import path
from .views import AdminProfileView,ChangePasswordView,WorkerProfileView,ProLandscaperWorkersView,ClientProfileView,ChangePasswordWorkerView,ChangePasswordLandscaperView,ChangePasswordClientView

urlpatterns = [
    # profile for whole role 
    path("admin/profile/", AdminProfileView.as_view(), name="admin-profile"),
    path("worker/profile/", WorkerProfileView.as_view(), name="worker-profile"),
    path("pro-landscaper/workers/", ProLandscaperWorkersView.as_view(), name="pro-landscaper-workers"),
    path("client/profile/", ClientProfileView.as_view(), name="client-profile"),
    # change password for whole role 
    path('admin/change-password/',ChangePasswordView.as_view(), name="change-password"),
    path('client/change-password/',ChangePasswordClientView.as_view(), name="change-password"),
    path('landscaper/change-password/',ChangePasswordLandscaperView.as_view(), name="change-password"),
    path('worker/change-password/',ChangePasswordWorkerView.as_view(), name="change-password"),

]
