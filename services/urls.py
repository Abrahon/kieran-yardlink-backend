from django.urls import path
from .views import (

    # -------- Client --------
    ClientServicePreferenceAPIView,
    ClientPreferenceNoteUpdateAPIView,
    ClientServiceOverviewAPIView,
    ClientJobHistoryAPIView,

    # -------- Schedule / Job --------
    LandscaperCompleteJobAPIView,
    RescheduleServiceAPIView,
    ServiceOverviewAPIView,
    # CompletedJobsAPIView,
    RecentActivityAPIView,
    # RecentJobCompletionAPIView
)


urlpatterns = [


    # ================= CLIENT =================

    # Client selects services + frequency
    path(
        "client/service-preference/",
        ClientServicePreferenceAPIView.as_view(),
        name="client-service-preference"
    ),

    # Client updates only note
    path(
        "client/service-preference/note/",
        ClientPreferenceNoteUpdateAPIView.as_view(),
        name="client-service-note"
    ),

    # Client dashboard overview (next schedule, previous job, payment)
    path(
        "client/service-overview/",
        ClientServiceOverviewAPIView.as_view(),
        name="client-service-overview"
    ),

    # Client completed job history (with images)
    path(
        "client/job-history/",
        ClientJobHistoryAPIView.as_view(),
        name="client-job-history"
    ),
    # schedule

    # ================= LANDSCAPER =================


    path("service-overview/", ServiceOverviewAPIView.as_view()),

    path("activity/recent/", RecentActivityAPIView.as_view(), name="recent-activity"),
    # path("add-ons/", AddOnServiceAPIView.as_view(), name="addon-services-list-create"),
    # path("add-ons/<int:service_id>/", AddOnServiceDetailAPIView.as_view(), name="addon-services-delete"),



]
