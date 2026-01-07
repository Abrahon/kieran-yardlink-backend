from django.urls import path
from .views import ServiceListCreateView, ServiceDetailView,ClientServicePreferenceView

urlpatterns = [
    path("services/", ServiceListCreateView.as_view(), name="service-list-create"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),
    # client
    path("services/preferences/", ClientServicePreferenceView.as_view()),
]
