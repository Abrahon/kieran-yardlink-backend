# from django.urls import path
# # from .views import accept_invite_page
# from .views import (
#     SendInvitationView,
#     AcceptInvitationView,
#     PendingInvitationListView,
#     CancelInvitationView,
#     DeleteInvitationView,
#     WorkerBlockToggleView,
#     AcceptedInvitationListView,
#     accept_invite_page
#     # AcceptedWorkerListView
# )

# urlpatterns = [
#     path("send/invite/", SendInvitationView.as_view()),
#     path("pending/", PendingInvitationListView.as_view()),
#     path("cancel/<int:invitation_id>/", CancelInvitationView.as_view()),
#     path("delete/<int:invitation_id>/", DeleteInvitationView.as_view()),
#     # path("accept-invite/<uuid:token>/", AcceptInvitationView.as_view()),
#     path(
#         "accept-invite/<uuid:token>/",
#         accept_invite_page,
#         name="accept-invite-page"
#     ),

#     path(
#         "accept-invite-api/<uuid:token>/",
#         AcceptInvitationView.as_view(),
#         name="accept-invite-api"
#     ),

#     path(
#         "workers/<int:worker_id>/block-toggle/",
#         WorkerBlockToggleView.as_view(),
#         name="worker-block-toggle"
#     ),
#     path(
#         "invitations/accepted/",
#         AcceptedInvitationListView.as_view(),
#         name="accepted-invitations"
#     ),
#     # path(
#     #     "workers/accepted/",
#     #     AcceptedWorkerListView.as_view(),
#     #     name="accepted-workers"
#     # ),

# ]

from django.urls import path
from .views import (
    SendInvitationView,
    AcceptInvitationView,
    PendingInvitationListView,
    CancelInvitationView,
    DeleteInvitationView,
    WorkerBlockToggleView,
    AcceptedInvitationListView,
)
from .views import accept_invite_page

urlpatterns = [
    # API endpoints
    path("send/invite/", SendInvitationView.as_view(), name="send-invite"),
    path("pending/", PendingInvitationListView.as_view(), name="pending-invitations"),
    path("cancel/<int:invitation_id>/", CancelInvitationView.as_view(), name="cancel-invitation"),
    path("delete/<int:invitation_id>/", DeleteInvitationView.as_view(), name="delete-invitation"),
    # invitations/urls.py
    path(
        "accept-invite-api/<uuid:token>/",
        AcceptInvitationView.as_view(),
        name="accept-invite-api"
    ),

    path("workers/<int:worker_id>/block-toggle/", WorkerBlockToggleView.as_view(), name="worker-block-toggle"),
    path("invitations/accepted/", AcceptedInvitationListView.as_view(), name="accepted-invitations"),
]
