from django.urls import path
from .views import (
    PropertyListCreateView,
    PropertyDetailView,
    PropertyMultipleImageUploadView,
    # PropertyDetailAPIView
)

urlpatterns = [
    # --------------------------
    # Properties
    # --------------------------
    path(
        "properties/",
        PropertyListCreateView.as_view(),
        name="property-list-create"
    ),
    path(
        "property/<int:pk>/",
        PropertyDetailView.as_view(),
        name="property-detail"
    ),

    # --------------------------
    # Upload multiple images for a property
    # --------------------------
    path(
        "properties/<int:property_id>/images/",
        PropertyMultipleImageUploadView.as_view(),
        name="property-image-upload"
    ),
    #  path("property/<int:property_id>/", PropertyDetailAPIView.as_view(), name="property-detail"),
]
