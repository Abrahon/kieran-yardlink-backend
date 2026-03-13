from rest_framework import generics, permissions
from jobs.models import Job
from jobs.serializers import JobSerializer  # Make sure you have this serializer
from django.utils import timezone

class UpcomingJobsListView(generics.ListAPIView):
    """
    List all upcoming jobs for the logged-in landscaper.
    """
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        landscaper = getattr(self.request.user, "landscaper_profile", None)
        if not landscaper:
            return Job.objects.none()

        return Job.objects.filter(
            landscaper=landscaper,
            status=Job.Status.UPCOMING,
            is_active=True,
            scheduled_date__gte=timezone.now().date()
        ).order_by("scheduled_date", "scheduled_time")