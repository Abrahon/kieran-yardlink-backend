# properties/urls.py
from django.urls import path
from .views import (
    PropertyListCreateView,
    PropertyDetailView,
    PropertyMultipleImageUploadView)
urlpatterns = [
        # Property URLs
    path('properties/', PropertyListCreateView.as_view(), name='property-list-create'),
    path('properties/<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),
    path("properties/images/upload/",PropertyMultipleImageUploadView.as_view(),name="property-image-array-upload"),


]
