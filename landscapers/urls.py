from django.urls import path
from .views import (
    CompleteLandscaperProfileView,
    GetBusinessProfileView,
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
    WorkingHoursUpdateView,
    WorkingHoursDeleteView,
    toggle_working_hour,
    get_landscaper_available_dates,
    get_landscaper_available_slots,
    ServiceAddonListView,
    ClientAcceptedServiceListView,
    ServiceQuoteCreateView,
    ServiceQuoteCounterView,
    ServiceQuoteActionView,
    ServiceQuoteListForLandscaper,
    ClientCounterOfferListView,
    get_landscaper_availability,
    ServiceQuoteDeleteView,
    get_landscaper_services

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
     # Client booking selection
    path("landscapers/<int:landscaper_id>/services/", get_landscaper_services, name="landscaper-services"),
    path("services/<int:service_id>/addons/", ServiceAddonListView.as_view(), name="service-addons"),

    # taggle 
    path('services/<int:pk>/toggle/', toggle_service_active, name='toggle-service-active'),

    # custom service
    path('client/custom-services/', ClientCustomServiceListCreateView.as_view(), name="client-custom-service-list-create"),
    path('client/custom-services/<int:pk>/', ClientCustomServiceRetrieveDestroyView.as_view(), name="client-custom-service-detail"),
    path("client/custom-services/accepted/",ClientAcceptedServiceListView.as_view(),name="client-accepted-services"),
    path("client/custom-services/<int:pk>/confirm/",client_confirm_service, name="client-confirm-service"),
    # List all client custom services for landscaper (filter by status if needed)
    path('landscaper/custom-service-requests/',LandscaperCustomServicePendingListView.as_view(), name='landscaper-custom-service-list'),
    # Accept a pending service
    path('landscaper/custom-service-requests/<int:pk>/accept/',landscaper_accept_service,name="landscaper-accept-custom-service"),

    path('client/custom-services/<int:pk>/toggle/', toggle_client_custom_service_active, name='toggle-client-custom-service'),

    # add ons
    path("addons/", AddonListCreateView.as_view(), name="addon-list-create"),
    path("addons/<int:pk>/", AddonDetailView.as_view(), name="addon-detail"),

    # landscaper search
    path('working-hours/', WorkingHoursListCreateView.as_view(), name='working-hours'),

    path(
        "working-hours/<int:pk>/update/",
        WorkingHoursUpdateView.as_view(),
        name="update-working-hour"
    ),

    path(
        "working-hours/<int:pk>/delete/",
        WorkingHoursDeleteView.as_view(),
        name="delete-working-hour"
    ),

    path(
        "working-hours/<int:pk>/toggle/",
        toggle_working_hour,
        name="toggle-working-hour"
    ),
        path(
        "client/<int:landscaper_id>/available-dates/",
        get_landscaper_available_dates
    ),

    path(
        "client/<int:landscaper_id>/available-slots/",
        get_landscaper_available_slots
    ),
    path(
        "landscapers/<int:landscaper_id>/availability/",
        get_landscaper_availability
    ),

    path("services/stats/", ServiceStatsAPIView.as_view(), name="service-stats"),
    path("services/performance/", service_performance_monthly, name="service-performance-monthly"),
    path("services/<int:service_id>/pin/", toggle_service_pin, name="service-pin"),


    path("quotes/create/", ServiceQuoteCreateView.as_view()),
    path("quotes/landscaper/", ServiceQuoteListForLandscaper.as_view()),
    path("quotes/<int:pk>/counter/", ServiceQuoteCounterView.as_view()),
    path("quotes/<int:pk>/action/", ServiceQuoteActionView.as_view()),
    path("quotes/counter-list/", ClientCounterOfferListView.as_view()),
    # optional
    path("quotes/<int:pk>/delete/",ServiceQuoteDeleteView.as_view(),name="quote-delete")
]
