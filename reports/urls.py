# analytics/urls.py or overview/urls.py

from django.urls import path
from .views import TrackVisitAPIView,AdminAcquisitionFunnelView,AdminConversionMetricsView,UserConcentrationByRegionView

urlpatterns = [
    path("admin/track-visit/", TrackVisitAPIView.as_view(), name="track-visit"),
    # analytics/urls.py or overview/urls.py
    path(
        "admin/analytics/acquisition-funnel/",
        AdminAcquisitionFunnelView.as_view(),
        name="admin-acquisition-funnel",
    ),
    path(
        "admin/analytics/conversion-metrics/",
        AdminConversionMetricsView.as_view(),
        name="admin-conversion-metrics"
    ),
    path(
    "admin/analytics/user-concentration-region/",
    UserConcentrationByRegionView.as_view(),
    name="admin-user-concentration-by-region",
)

]
