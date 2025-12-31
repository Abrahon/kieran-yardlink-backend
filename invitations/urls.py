# invitations/urls.py
from django.urls import path
from .views import SendInvitationView, AcceptInvitationView

urlpatterns = [
    path("send/invite/", SendInvitationView.as_view()),
    path("accept-invite/<uuid:token>/", AcceptInvitationView.as_view()),
]
