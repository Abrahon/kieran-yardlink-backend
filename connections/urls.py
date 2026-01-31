
from django.urls import path
from .views import (
    SendConnectionRequestAPIView,
    InboxConnectionRequestAPIView,
    SentConnectionRequestAPIView,
    RespondConnectionRequestAPIView,
    CancelConnectionRequestAPIView,
    AcceptedConnectionsAPIView,
    AcceptConnectionAPIView,
    RemoveConnectionAPIView,
    UpcomingJobAPIView,
)

urlpatterns = [
    # Send a new connection request
    path(
        "connections/send/",
        SendConnectionRequestAPIView.as_view(),
        name="send-connection-request"
    ),

    # View pending connection requests received (inbox)
    path(
        "connections/inbox/",
        InboxConnectionRequestAPIView.as_view(),
        name="inbox-connection-requests"
    ),

    # View connection requests sent by the current user
    path(
        "connections/sent/",
        SentConnectionRequestAPIView.as_view(),
        name="sent-connection-requests"
    ),

    # Respond (accept/reject) to a connection request
    path(
        "connections/respond/<int:pk>/",
        RespondConnectionRequestAPIView.as_view(),
        name="respond-connection-request"
    ),

    # Cancel a pending request sent by the current user
    path(
        "connections/cancel/<int:pk>/",
        CancelConnectionRequestAPIView.as_view(),
        name="cancel-connection-request"
    ),

    # Accept a connection request and auto-schedule a job
    path(
        "connections/accept/<int:request_id>/",
        AcceptConnectionAPIView.as_view(),
        name="accept-connection-request"
    ),

    # List all accepted connections (friend list) with optional upcoming jobs
    path(
        "connections/accepted/",
        AcceptedConnectionsAPIView.as_view(),
        name="accepted-connections"
    ),

    # Get the next upcoming job for a connection
    path(
        "upcoming-job/<int:pk>/",
        UpcomingJobAPIView.as_view(),
        name="upcoming-job"
    ),
    path(
        "upcoming-job/list/",
        AcceptConnectionAPIView.as_view(),
        name="upcoming-job"
    ),

    # Remove an accepted connection
    path(
        "connections/remove/<int:connection_id>/",
        RemoveConnectionAPIView.as_view(),
        name="remove-connection"
    ),
]
