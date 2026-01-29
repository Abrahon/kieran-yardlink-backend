from django.urls import path
from .views import JobCreateAPIView, JobListAPIView, JobRetrieveUpdateAPIView

urlpatterns = [
    path("job/create/", JobCreateAPIView.as_view(), name="job-create"),
    path("job/list/", JobListAPIView.as_view(), name="job-list"),
    path("job/<int:pk>/", JobRetrieveUpdateAPIView.as_view(), name="job-detail"),
]
