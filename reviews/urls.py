from django.urls import path
from .views import (
    AddOrUpdateReviewAPIView,
    LandscaperReviewListAPIView,
    DeleteReviewAPIView
)

urlpatterns = [
    path(
        "landscapers/<int:landscaper_id>/add-review/",
        AddOrUpdateReviewAPIView.as_view(),
        name="add-update-review"
    ),
    path(
        "landscapers/<int:landscaper_id>/reviews/",
        LandscaperReviewListAPIView.as_view(),
        name="landscaper-reviews"
    ),
    path(
        "reviews/<int:review_id>/delete/",
        DeleteReviewAPIView.as_view(),
        name="delete-review"
    ),
]
