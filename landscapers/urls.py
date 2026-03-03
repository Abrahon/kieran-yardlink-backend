from django.urls import path
from .views import (
    CompleteLandscaperProfileView,
    GetBusinessProfileView,
    LandscaperFind,
    WorkingHoursListCreateView,
    ServiceListCreateView,
    ServiceDetailView,
    UpdateBusinessProfileView,
    ServiceDetailView,
    toggle_service_active,
    service_performance_monthly,
    toggle_service_pin,
    ClientCustomServiceListCreateView,
    ClientCustomServiceDetailView,
    AddonListCreateView,
    AddonDetailView

)


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path(
        "landscaper/profile/update/",
        UpdateBusinessProfileView.as_view(),
        name="landscaper-profile-update"
    ),
    path("landscaper/profile/", GetBusinessProfileView.as_view(), name="get-landscaper-profile"),
    
    # standard service crud 
    path("services/", ServiceListCreateView.as_view(), name="service-list-create"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),

    # taggle 
    path('services/standard/<int:pk>/toggle/', toggle_service_active, name='toggle-service-active'),

    # custom service
    path("custom-services/", ClientCustomServiceListCreateView.as_view(), name="custom-service-list-create"),
    path("custom-services/<int:pk>/", ClientCustomServiceDetailView.as_view(), name="custom-service-detail"),

    # add ons
    path("addons/", AddonListCreateView.as_view(), name="addon-list-create"),
    path("addons/<int:pk>/", AddonDetailView.as_view(), name="addon-detail"),


    # landscaper search
    path("landscapers/search/", LandscaperFind.as_view(), name="landscaper-search"),
    path('working-hours/', WorkingHoursListCreateView.as_view(), name='working-hours'),

    # path("services/stats/", ServiceStatsAPIView.as_view(), name="service-stats"),
    path("services/performance/", service_performance_monthly, name="service-performance-monthly"),
    path("services/<int:service_id>/pin/", toggle_service_pin, name="service-pin"),


]
