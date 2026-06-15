from django.urls import path
from .views import (

    # -------- Client --------
    ClientServicePreferenceAPIView,
    ClientPreferenceNoteUpdateAPIView,
    # ClientServiceOverviewAPIView,
    ClientJobHistoryAPIView,

    # -------- Schedule / Job --------
    LandscaperCompleteJobAPIView,
    RescheduleServiceAPIView,
    ServiceOverviewAPIView,
    RecentActivityAPIView,
    # RecentJobCompletionAPIView
)


urlpatterns = [

    # ================= CLIENT =================

    path(
        "client/service-preference/",
        ClientServicePreferenceAPIView.as_view(),
        name="client-service-preference"
    ),
    path(
        "client/service-preference/note/",
        ClientPreferenceNoteUpdateAPIView.as_view(),
        name="client-service-note"
    ),

    # Client dashboard overview (next schedule, previous job, payment)
    # path(
    #     "client/service-overview/",
    #     ClientServiceOverviewAPIView.as_view(),
    #     name="client-service-overview"
    # )


    path("service-overview/", ServiceOverviewAPIView.as_view()),

    path("activity/recent/", RecentActivityAPIView.as_view(), name="recent-activity"),
]
