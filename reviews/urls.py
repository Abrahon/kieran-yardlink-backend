from django.urls import path
from .views import (
    AddOrUpdateReviewAPIView,
    LandscaperReviewListAPIView,
    DeleteReviewAPIView
)

urlpatterns = [
    path(
        "landscapers/<int:landscaper_id>/review/",
        AddOrUpdateReviewAPIView.as_view()
    ),
    path(
        "landscapers/<int:landscaper_id>/reviews/",
        LandscaperReviewListAPIView.as_view()
    ),
    path(
        "reviews/<int:review_id>/delete/",
        DeleteReviewAPIView.as_view()
    ),
]
