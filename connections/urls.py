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
    path("connections/send/", SendConnectionRequestAPIView.as_view()),
    path("connections/inbox/", InboxConnectionRequestAPIView.as_view()),
    path("connections/sent/", SentConnectionRequestAPIView.as_view()),
    path("connections/respond/<int:pk>/", RespondConnectionRequestAPIView.as_view()),
    path("connections/cancel/<int:pk>/", CancelConnectionRequestAPIView.as_view()),
    # path("connections/accepted/", AcceptedConnectionsAPIView.as_view()),
]
