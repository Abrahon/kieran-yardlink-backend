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
    AddonListCreateView,
    AddonDetailView,
    ServiceStatsAPIView,
    ClientCustomServiceRetrieveDestroyView,
    # ClientCustomServiceDeleteView,
    toggle_client_custom_service_active,
    ClientCustomServiceListCreateView,
    LandscaperCustomServicePendingListView,
    client_confirm_service,
    landscaper_accept_service,

)


urlpatterns = [
    path("business/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path(
        "business/profile/update/",
        UpdateBusinessProfileView.as_view(),
        name="landscaper-profile-update"
    ),
    path("business/profile/", GetBusinessProfileView.as_view(), name="get-landscaper-profile"),
    
    # standard service crud 
    path("services/", ServiceListCreateView.as_view(), name="service-list-create"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),

    # taggle 
    path('services/<int:pk>/toggle/', toggle_service_active, name='toggle-service-active'),

    # custom service
    path('client/custom-services/', ClientCustomServiceListCreateView.as_view(), name='client-custom-services'),
    path('client/custom-services/<int:pk>/', ClientCustomServiceRetrieveDestroyView.as_view(), name='client-custom-service-update'),
    path("client/custom-services/<int:pk>/confirm/",client_confirm_service, name="client-custom-service-confirm"),

    path('client/custom-services/<int:pk>/toggle/', toggle_client_custom_service_active, name='toggle-client-custom-service'),
    
    # List all client custom services for landscaper (filter by status if needed)
    path('landscaper/custom-service-requests/',LandscaperCustomServicePendingListView.as_view(), name='landscaper-custom-service-list'),
    # Accept a pending service
    path('landscaper/custom-service-requests/<int:pk>/',landscaper_accept_service,name="landscaper-accept-custom-service"),

    # add ons
    path("addons/", AddonListCreateView.as_view(), name="addon-list-create"),
    path("addons/<int:pk>/", AddonDetailView.as_view(), name="addon-detail"),


    # landscaper search
    path("landscapers/search/", LandscaperFind.as_view(), name="landscaper-search"),
    path('working-hours/', WorkingHoursListCreateView.as_view(), name='working-hours'),

    path("services/stats/", ServiceStatsAPIView.as_view(), name="service-stats"),
    path("services/performance/", service_performance_monthly, name="service-performance-monthly"),
    path("services/<int:service_id>/pin/", toggle_service_pin, name="service-pin"),


]
