from django.urls import path
from .views import (
    # -------- Services --------
    StandardServiceListAPIView,
    StandardServiceCreateAPIView,
    CustomServiceCreateAPIView,

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
    ServiceScheduleDetailAPIView
)


urlpatterns = [

    # ================= SERVICES =================

    # List standard services (Client / Landscaper)
    path("services/standard/", StandardServiceListAPIView.as_view(), name="standard-services"),

    # Admin adds standard service
    path("services/standard/add/", StandardServiceCreateAPIView.as_view(), name="add-standard-service"),

    # Landscaper adds custom service
    path("services/custom/add/", CustomServiceCreateAPIView.as_view(), name="add-custom-service"),


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
    path(    
        "schedule/<int:schedule_id>/reschedule/",
        RescheduleServiceAPIView.as_view(),
        name="reschedule-service"
    ),
    # ================= LANDSCAPER =================

    # Landscaper marks a scheduled job as completed + uploads images
    path(
        "landscaper/schedule/<int:schedule_id>/complete/",
        LandscaperCompleteJobAPIView.as_view(),
        name="landscaper-complete-job"
    ),

    # List all completed jobs for logged-in landscaper
    path("completed-job/list/", CompletedJobsAPIView.as_view(), name="completed-jobs"),

    path("service-overview/", ServiceOverviewAPIView.as_view()),
    path(
        "schedule/<int:schedule_id>/",
        ServiceScheduleDetailAPIView.as_view(),
        name="schedule-detail"
),

]
