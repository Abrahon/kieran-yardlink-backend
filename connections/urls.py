

# from django.urls import path
# from .views import (
#     SendConnectionRequestAPIView,
#     InboxConnectionRequestAPIView,
#     SentConnectionRequestAPIView,
#     RespondConnectionRequestAPIView,
#     CancelConnectionRequestAPIView,
#     AcceptedConnectionsAPIView,
#     # AcceptConnectionAPIView,
#     RemoveConnectionAPIView,
#     UpcomingJobListAPIView,
#     JobDetailAPIView,
#     UpcomingServicesForClientAPIView,
#     ClientUpcomingServiceAPIView,
#     ClientCompletedServiceAPIView,
#     ConnectedClientListAPIView,
#     TodayJobsAPIView
    
# )

# urlpatterns = [
#     # Send a new connection request
#     path(
#         "connections/send/",
#         SendConnectionRequestAPIView.as_view(),
#         name="send-connection-request"
#     ),

#     # View pending connection requests received (inbox)
#     path(
#         "connections/inbox/",
#         InboxConnectionRequestAPIView.as_view(),
#         name="inbox-connection-requests"
#     ),

#     # View connection requests sent by the current user
#     path(
#         "connections/sent/",
#         SentConnectionRequestAPIView.as_view(),
#         name="sent-connection-requests"
#     ),

#     # Respond (accept/reject) to a connection request
#     path(
#         "connections/respond/<int:pk>/",
#         RespondConnectionRequestAPIView.as_view(),
#         name="respond-connection-request"
#     ),

#     # Cancel a pending request sent by the current user
#     path(
#         "connections/cancel/<int:pk>/",
#         CancelConnectionRequestAPIView.as_view(),
#         name="cancel-connection-request"
#     ),

#     # List all accepted connections (friend list) with optional upcoming jobs
#     path(
#         "connections/accepted/",
#         AcceptedConnectionsAPIView.as_view(),
#         name="accepted-connections"
#     ),

#     # Get the next upcoming job for a connection
#     path(
#         "upcoming-job/<int:pk>/",
#         UpcomingJobListAPIView.as_view(),
#         name="upcoming-job"
#     ),
#     path(
#         "upcoming-job/list/",
#         UpcomingJobListAPIView.as_view(),
#         name="upcoming-job"
#     ),
    
#     path("jobs/<int:job_id>/", JobDetailAPIView.as_view(), name="job-detail"),

#     # Remove an accepted connection
#     path(
#         "connections/remove/<int:connection_id>/",
#         RemoveConnectionAPIView.as_view(),
#         name="remove-connection"
#     ),
#     path('client/upcoming-services/', UpcomingServicesForClientAPIView.as_view(), name='client-upcoming-services'),
#     path('services/upcoming/<int:service_id>/', ClientUpcomingServiceAPIView.as_view(), name='client-reschedule-service'),

#     # Completed services (GET only)
#     path('services/completed/', ClientCompletedServiceAPIView.as_view(), name='client-completed-services'),
#     #  path("jobs/<int:job_id>/client-location/", ClientLocationAPIView.as_view()),
#     path("connections/clients/", ConnectedClientListAPIView.as_view()),
#     # urls.py
#     path("jobs/today/", TodayJobsAPIView.as_view(), name="todays-jobs"),

# ]

from django.urls import path
from .views import (
    SendConnectionRequestAPIView,
    InboxConnectionRequestAPIView,
    SentConnectionRequestAPIView,
    RespondConnectionRequestAPIView,
    CancelConnectionRequestAPIView,
    AcceptedConnectionsAPIView,
    RemoveConnectionAPIView,
    ConnectedClientListAPIView,

)

urlpatterns = [
    path("connections/send/", SendConnectionRequestAPIView.as_view(), name="send-connection-request"),
    path("connections/inbox/", InboxConnectionRequestAPIView.as_view(), name="inbox-connection-requests"),
    path("connections/sent/", SentConnectionRequestAPIView.as_view(), name="sent-connection-requests"),
    path("connections/respond/<int:pk>/", RespondConnectionRequestAPIView.as_view(), name="respond-connection-request"),
    path("connections/cancel/<int:pk>/", CancelConnectionRequestAPIView.as_view(), name="cancel-connection-request"),
    path("connections/accepted/", AcceptedConnectionsAPIView.as_view(), name="accepted-connections"),
    path("connections/remove/<int:connection_id>/", RemoveConnectionAPIView.as_view(), name="remove-connection"),
    path("connections/clients/", ConnectedClientListAPIView.as_view(), name="connected-client-list"),


]