
from django.urls import path
from .views import (
    SendInvitationView,
    AcceptInvitationView,
    PendingInvitationListView,
    CancelInvitationView,
    DeleteInvitationView,
    WorkerBlockToggleView,
    AcceptedInvitationListView,
    BlockedWorkerListView,
    accept_invitation_page,
    invitation_success
)
# from .views import accept_invite_page

urlpatterns = [
    # API endpoints
    path("send/invite/", SendInvitationView.as_view(), name="send-invite"),
    path("pending/", PendingInvitationListView.as_view(), name="pending-invitations"),
    path("cancel/<int:invitation_id>/", CancelInvitationView.as_view(), name="cancel-invitation"),
    path("delete/<int:invitation_id>/", DeleteInvitationView.as_view(), name="delete-invitation"),
    # invitations/urls.py
    path("accept-invite/<uuid:token>/",AcceptInvitationView.as_view(),name="accept-invite-api"),
    path("invitations/accept/<uuid:token>/",accept_invitation_page, name="accept-invitation-page"),
    path("invitation-success/",invitation_success,name="invitation-success"),

    path("workers/<int:worker_id>/block-toggle/", WorkerBlockToggleView.as_view(), name="worker-block-toggle"),
    path("invitations/accepted/", AcceptedInvitationListView.as_view(), name="accepted-invitations"),
    path("blocked-list/", BlockedWorkerListView.as_view(), name="blocked-workers"),
]
