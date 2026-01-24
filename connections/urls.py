from django.urls import path
from .views import (
    SendConnectionRequestAPIView,
    InboxConnectionRequestAPIView,
    SentConnectionRequestAPIView,
    RespondConnectionRequestAPIView,
    CancelConnectionRequestAPIView,
    # AcceptedConnectionsAPIView,
)

urlpatterns = [
    path(
        "connections/send/",
        SendConnectionRequestAPIView.as_view(),
        name="send-connection-request"
    ),
    path(
        "connections/inbox/",
        InboxConnectionRequestAPIView.as_view(),
        name="inbox-connection-requests"
    ),
    path(
        "connections/sent/",
        SentConnectionRequestAPIView.as_view(),
        name="sent-connection-requests"
    ),
    path(
        "connections/respond/<int:pk>/",
        RespondConnectionRequestAPIView.as_view(),
        name="respond-connection-request"
    ),
    path(
        "connections/cancel/<int:pk>/",
        CancelConnectionRequestAPIView.as_view(),
        name="cancel-connection-request"
    ),
    # path(
    #     "connections/accepted/",
    #     AcceptedConnectionsAPIView.as_view(),
    #     name="accepted-connections"
    # ),
]
