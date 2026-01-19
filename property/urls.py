# properties/urls.py
from django.urls import path
from .views import (
    PropertyListCreateView,
    PropertyDetailView,
    PropertyMultipleImageUploadView,
    PropertyImagesListView)


urlpatterns = [
    path("properties/", PropertyListCreateView.as_view()),
    path("properties/<int:pk>/", PropertyDetailView.as_view()),
    path("properties/images/", PropertyMultipleImageUploadView.as_view()),
    path("properties/images/<int:property_id>/", PropertyImagesListView.as_view()),
]
