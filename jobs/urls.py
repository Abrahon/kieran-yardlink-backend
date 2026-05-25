

from django.urls import path
from jobs.views import (
    UpcomingJobsListView,
    JobDetailView,
    # AddJobItemsView,
    toggle_job_item_completion,
    JobImageCreateView,
    JobRescheduleCreateView,
    add_job_note,
    CompletedJobsListView,
    ManualOneTimeJobCreateView,
    InProgressJobsListView,
    InProgressJobDetailView,
    CompletedJobDetailView,
    ClientUnpaidCompletedJobView,
    ClientUpcomingJobsListView,
    update_job_status,
    ProblemJobsListView,
    ClientUpcomingServiceDetailView,
    PendingRescheduleListView,
    RescheduleActionView
)



urlpatterns = [
    path("landscaper/jobs/upcoming/", UpcomingJobsListView.as_view(), name="upcoming-jobs"),
    path("landscaper/jobs/in-progress/", InProgressJobsListView.as_view(), name="in-progress-jobs"),
    path("landscaper/jobs/in-progress/<int:id>/", InProgressJobDetailView.as_view(), name="in-progress-job-detail"),
    path("landscaper/jobs/<int:id>/", JobDetailView.as_view(), name="job-detail"),
    path("landscaper/jobs/items/<int:item_id>/toggle/", toggle_job_item_completion, name="job-item-toggle"),
    path("landscaper/jobs/<int:job_id>/note/", add_job_note, name="job-add-note"),
    path("landscaper/jobs/images/add/", JobImageCreateView.as_view(), name="job-add-image"),
    path("landscaper/jobs/reschedule/add/", JobRescheduleCreateView.as_view(), name="job-reschedule"),
    path("landscaper/jobs/completed/", CompletedJobsListView.as_view(), name="completed-jobs"),
    path("landscaper/jobs/completed/<int:pk>/",CompletedJobDetailView.as_view(),name="completed-job-detail"),

    # manual job created external client
    path("landscaper/manual-jobs/create/", ManualOneTimeJobCreateView.as_view(), name="manual-job-create"),
        # 🔹 Get single job details (items + images + price)
    path("client/job-history/",ClientUnpaidCompletedJobView.as_view(),name="client-job-detail"),

    # 🔹 Pay for completed job
    # path("client/jobs/<int:job_id>/pay/",client_pay_job,name="client-pay-job"),
    path("client/upcoming-service/", ClientUpcomingJobsListView.as_view()),
    # Upcoming service detail
    path("client/upcoming-services/<int:id>/",ClientUpcomingServiceDetailView.as_view(),name="client-upcoming-service-detail"),
    # path("jobs/reschedule/<int:pk>/approve/",ApproveJobRescheduleView.as_view(),name="job-reschedule-approve"),
    path("landscaper/jobs/<int:job_id>/status/", update_job_status, name="job-status-update"),
    path("landscaper/jobs/problem/", ProblemJobsListView.as_view(), name="problem-jobs"),
        # 📌 Pending reschedule list (landscaper dashboard)
    path(
        "reschedule/pending/",
        PendingRescheduleListView.as_view(),
        name="reschedule-pending-list"
    ),

    # 📌 Approve / Reject (single unified endpoint)
    path(
        "reschedule/<int:pk>/action/",
        RescheduleActionView.as_view(),
        name="reschedule-action"
    ),
]