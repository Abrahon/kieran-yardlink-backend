from django.urls import path
from .views import (
    SendInvitationView,
    AcceptInvitationView,
    PendingInvitationListView,
    CancelInvitationView,
    DeleteInvitationView,
    BlockWorkerView
)

urlpatterns = [
    path("send/invite/", SendInvitationView.as_view()),
    path("pending/", PendingInvitationListView.as_view()),
    path("cancel/<int:invitation_id>/", CancelInvitationView.as_view()),
    path("delete/<int:invitation_id>/", DeleteInvitationView.as_view()),
    path("accept-invite/<uuid:token>/", AcceptInvitationView.as_view()),
    path(
        "workers/block/<int:worker_id>/",
        BlockWorkerView.as_view(),
        name="block-worker"
    ),
]
