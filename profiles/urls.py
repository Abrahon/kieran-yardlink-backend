from django.urls import path
from .views import AdminProfileView,ChangePasswordView,WorkerProfileView,ProLandscaperWorkersView

urlpatterns = [
    path("admin/profile/", AdminProfileView.as_view(), name="admin-profile"),
    path('admin/change-password/',ChangePasswordView.as_view(), name="change-password"),
    # Worker profile
    path("worker/profile/", WorkerProfileView.as_view(), name="worker-profile"),
    path("pro-landscaper/workers/", ProLandscaperWorkersView.as_view(), name="pro-landscaper-workers"),
]
