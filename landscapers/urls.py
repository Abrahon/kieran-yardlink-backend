from django.urls import path
from .views import (
    CompleteLandscaperProfileView,
    GetLandscaperProfileView,
    LandscaperFind,WorkingHoursListCreateView,
    CreateServiceView,ListServicesView,
    UpdateLandscaperProfileView,
    UpdateServiceView,
    CreateCustomServiceAPIView,
    CustomServiceListAPIView,
    StandardServiceCreateAPIView,
    StandardServiceListAPIView,
    toggle_service_active,
    StandardServiceUpdateAPIView,
    ServiceStatsAPIView,
    service_performance_monthly,
    toggle_service_pin

)


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path(
        "landscaper/profile/update/",
        UpdateLandscaperProfileView.as_view(),
        name="landscaper-profile-update"
    ),
    path("landscaper/profile/", GetLandscaperProfileView.as_view(), name="get-landscaper-profile"),
    path("service/create/", CreateServiceView.as_view(), name="create-service"),
    path("services/", ListServicesView.as_view(), name="list-services"),
    path("landscapers/search/", LandscaperFind.as_view(), name="landscaper-search"),
    path('working-hours/', WorkingHoursListCreateView.as_view(), name='working-hours'),
    path("services/update/<int:id>/", UpdateServiceView.as_view()),
    path('services/custom/',CreateCustomServiceAPIView.as_view(), name='create-custom-service'),
    path('services/custom/list/', CustomServiceListAPIView.as_view(), name='list-custom-service'),
    path('services/standard/', StandardServiceCreateAPIView.as_view(), name='create-standard-service'),
    path('services/standard/list/', StandardServiceListAPIView.as_view(), name='list-standard-service'),
    path('services/standard/<int:pk>/toggle/', toggle_service_active, name='toggle-service-active'),
    path("services/<int:id>/edit/", StandardServiceUpdateAPIView.as_view(), name="edit-standard-service"),
    path("services/stats/", ServiceStatsAPIView.as_view(), name="service-stats"),
    path("services/performance/", service_performance_monthly, name="service-performance-monthly"),
    path("services/<int:service_id>/pin/", toggle_service_pin, name="service-pin"),


]
