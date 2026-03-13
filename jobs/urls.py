from django.urls import path
from jobs.views import UpcomingJobsListView

urlpatterns = [
    path('landscaper/jobs/upcoming/', UpcomingJobsListView.as_view(), name='upcoming-jobs'),
]