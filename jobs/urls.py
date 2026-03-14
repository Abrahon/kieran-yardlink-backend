from django.urls import path
from jobs.views import (
    UpcomingJobsListView,
    JobDetailView,
    JobImageCreateView,
    JobRescheduleCreateView,
    add_job_note,
)

urlpatterns = [
    # Upcoming jobs for landscaper
    path("landscaper/jobs/upcoming/", UpcomingJobsListView.as_view(), name="upcoming-jobs"),

    # Job details
    path("jobs/<int:id>/", JobDetailView.as_view(), name="job-detail"),

    # Add note to job
    path("jobs/<int:job_id>/add-note/", add_job_note, name="job-add-note"),

    # Upload job image
    path("jobs/images/add/", JobImageCreateView.as_view(), name="job-add-image"),

    # Reschedule job
    path("jobs/reschedule/add/", JobRescheduleCreateView.as_view(), name="job-reschedule"),
]