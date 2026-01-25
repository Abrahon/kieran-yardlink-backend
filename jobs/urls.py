from django.urls import path
from .views import JobCreateAPIView, JobUpdateAPIView

urlpatterns = [
    # Create a new job (POST)
    path("jobs/create/", JobCreateAPIView.as_view(), name="job-create"),

    # Update an existing job (PUT)
    path("jobs/update/<int:pk>/", JobUpdateAPIView.as_view(), name="job-update"),
]
