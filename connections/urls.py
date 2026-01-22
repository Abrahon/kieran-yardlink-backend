from django.urls import path
from .views import (
    SendConnectionRequestAPIView,
    RespondConnectionRequestAPIView,
    IncomingRequestsAPIView,
    MyConnectionsAPIView,
)

urlpatterns = [
    path("send/<int:user_id>/", SendConnectionRequestAPIView.as_view()),
    path("respond/<int:request_id>/", RespondConnectionRequestAPIView.as_view()),
    path("incoming/", IncomingRequestsAPIView.as_view()),
    path("my/", MyConnectionsAPIView.as_view()),
]
