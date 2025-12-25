from django.urls import path
from .views import CompleteLandscaperProfileView,GetLandscaperProfileView


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path("landscaper/profile/", GetLandscaperProfileView.as_view(), name="get-landscaper-profile")
]
