from django.urls import path
from .views import CompleteLandscaperProfileView,GetLandscaperProfileView,LandscaperFind


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path("landscaper/profile/", GetLandscaperProfileView.as_view(), name="get-landscaper-profile"),
    path("landscapers/search/", LandscaperFind.as_view(), name="landscaper-search"),
]
