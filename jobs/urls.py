# from django.urls import path
# from jobs.views import (
#     UpcomingJobsListView,
#     JobDetailView,
#     JobImageCreateView,
#     JobRescheduleCreateView,
#     add_job_note,
# )

# urlpatterns = [
#     # Upcoming jobs for landscaper
#     path("landscaper/jobs/upcoming/", UpcomingJobsListView.as_view(), name="upcoming-jobs"),

#     # Job details
#     path("landscapers/jobs/<int:id>/", JobDetailView.as_view(), name="job-detail"),

#     # Add note to job
#     path("jobs/<int:job_id>/add-note/", add_job_note, name="job-add-note"),

#     # Upload job image
#     path("jobs/images/add/", JobImageCreateView.as_view(), name="job-add-image"),

#     # Reschedule job
#     path("jobs/reschedule/add/", JobRescheduleCreateView.as_view(), name="job-reschedule"),
# ]

from django.urls import path
from jobs.views import (
    UpcomingJobsListView,
    JobDetailView,
    # AddJobItemsView,
    toggle_job_item_completion,
    JobImageCreateView,
    JobRescheduleCreateView,
    add_job_note,
    CompletedJobsListView
    # sync_job_items_from_client_services
)



urlpatterns = [
    path("landscaper/jobs/upcoming/", UpcomingJobsListView.as_view(), name="upcoming-jobs"),
    path("landscaper/jobs/<int:id>/", JobDetailView.as_view(), name="job-detail"),
    path("landscaper/jobs/items/<int:item_id>/toggle/", toggle_job_item_completion, name="job-item-toggle"),
    path("landscaper/jobs/<int:job_id>/note/", add_job_note, name="job-add-note"),
    path("landscaper/jobs/images/add/", JobImageCreateView.as_view(), name="job-add-image"),
    path("landscaper/jobs/reschedule/add/", JobRescheduleCreateView.as_view(), name="job-reschedule"),
    path("landscaper/jobs/completed/", CompletedJobsListView.as_view(), name="completed-jobs"),
]