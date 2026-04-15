

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
    InProgressJobDetailView
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
    # manual job created
    path("landscaper/manual-jobs/create/", ManualOneTimeJobCreateView.as_view(), name="manual-job-create"),
]