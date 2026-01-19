# from django.urls import path
# from .views import ServiceListCreateView, ServiceDetailView,ClientServicePreferenceView

# urlpatterns = [
#     path("services/", ServiceListCreateView.as_view(), name="service-list-create"),
#     path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),
#     # client
#     path("services/preferences/", ClientServicePreferenceView.as_view()),
# ]
# from django.urls import path
# from .views import (
#     ClientServiceOverviewAPIView,
#     ClientServicePreferenceAPIView,
#     StandardServiceListAPIView
# )

# urlpatterns = [
#     path("client/service-overview/", ClientServiceOverviewAPIView.as_view()),
#     path("services/preferences/", ClientServicePreferenceAPIView.as_view()),
#     path("services/standard/", StandardServiceListAPIView.as_view()),
# ]
from django.urls import path
from .views import (
    ClientServiceOverviewAPIView,
    ClientServicePreferenceAPIView,
    StandardServiceListAPIView,
    StandardServiceCreateAPIView,
    CustomServiceCreateAPIView,
    ClientPreferenceNoteUpdateAPIView,  # new import
)

urlpatterns = [
    # Standard services
    path("services/standard/", StandardServiceListAPIView.as_view()),
    path("services/standard/add/", StandardServiceCreateAPIView.as_view()),
    
    # Custom services
    path("services/custom/add/", CustomServiceCreateAPIView.as_view()),
    
    # Client preferences
    path("client/service-preference/", ClientServicePreferenceAPIView.as_view()),  # GET/PATCH/PUT full
    path("client/service-preference/note/", ClientPreferenceNoteUpdateAPIView.as_view()),  # POST note only
    
    # Client overview
    path("client/service-overview/", ClientServiceOverviewAPIView.as_view()),
]
