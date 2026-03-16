
from django.urls import path
from .views import (
    AdminProfileView,
    ChangePasswordView,
    WorkerProfileView,
    ProLandscaperWorkersView,
    ClientProfileView,
    ChangePasswordWorkerView,
    ChangePasswordLandscaperView,
    ChangePasswordClientView,
    LandScaperProfileView,
    ChangePasswordAPIView,
    AllLandscapersListView,
    ClientProfileListView,
    LandscaperSearchByKMAPIView,
    ClientSearchByKMAPIView,
    LandscaperDetailWithChatView,
    ClientDetailWithChatView,
    ReminderToggleAPIView,
    LandscaperReminderToggleAPIView,
    ClientReminderToggleAPIView,
    LandscaperPersonalProfileView,
    ExternalClientListCreateView,
    ExternalClientDetailView,
)

urlpatterns = [
    # -------------------- Profiles -------------------- #
    path("admin/profile/", AdminProfileView.as_view(), name="admin-profile"),
    path("worker/profile/", WorkerProfileView.as_view(), name="worker-profile"),
    path("landscaper/profile/", LandscaperPersonalProfileView.as_view(), name="pro-landscaper-profile"),
    path("landscaper/profiles/", LandScaperProfileView.as_view(), name="pro-landscaper-profile"),
    path("pro-landscaper/workers/", ProLandscaperWorkersView.as_view(), name="pro-landscaper-workers"),
    path("client/profile/", ClientProfileView.as_view(), name="client-profile"),

    # -------------------- Change Password -------------------- #
    path("admin/change-password/", ChangePasswordView.as_view(), name="admin-change-password"),
    path("worker/change-password/", ChangePasswordWorkerView.as_view(), name="worker-change-password"),
    path("landscaper/change-password/", ChangePasswordLandscaperView.as_view(), name="landscaper-change-password"),
    path("client/change-password/", ChangePasswordClientView.as_view(), name="client-change-password"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),  # generic endpoint

    # -------------------- Lists -------------------- #
    path("landscapers-list/", AllLandscapersListView.as_view()),
    path("clients-list/", ClientProfileListView.as_view(), name="client-list"),
    path("landscapers/search/", LandscaperSearchByKMAPIView.as_view()),
    path("clients/search/", ClientSearchByKMAPIView.as_view()),
    # user details
    path("landscaper/profile/<int:id>/", LandscaperDetailWithChatView.as_view(), name="landscaper_detail_chat"),
    path("client/profile/<int:id>/", ClientDetailWithChatView.as_view(), name="client_detail_chat"),
    # profiles/urls.py

    path("reminder-toggle/", ReminderToggleAPIView.as_view(), name="reminder-toggle"),

    path("landscaper/reminders/", LandscaperReminderToggleAPIView.as_view(), name="landscaper-reminders"),
    path("client/reminders/", ClientReminderToggleAPIView.as_view(), name="client-reminders"),

    path(
        "landscaper/external-clients/",
        ExternalClientListCreateView.as_view(),
        name="external-client-list-create"
    ),
    path(
        "landscaper/external-clients/<int:pk>/",
        ExternalClientDetailView.as_view(),
        name="external-client-detail"
    ),

]
