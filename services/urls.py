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
    CompletedJobsAPIView,
    ServiceScheduleDetailAPIView,
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

    # Landscaper marks a scheduled job as completed + uploads images
    # path(
    #     "landscaper/schedule/<int:schedule_id>/complete/",
    #     LandscaperCompleteJobAPIView.as_view(),
    #     name="landscaper-complete-job"
    # ),

    # List all completed jobs for logged-in landscaper
    # path("completed-job/list/", CompletedJobsAPIView.as_view(), name="completed-jobs"),

    path("service-overview/", ServiceOverviewAPIView.as_view()),
    path(
        "schedule/<int:schedule_id>/",
        ServiceScheduleDetailAPIView.as_view(),
        name="schedule-detail"

    ),
    path("activity/recent/", RecentActivityAPIView.as_view(), name="recent-activity"),
    # path("add-ons/", AddOnServiceAPIView.as_view(), name="addon-services-list-create"),
    # path("add-ons/<int:service_id>/", AddOnServiceDetailAPIView.as_view(), name="addon-services-delete"),



]
