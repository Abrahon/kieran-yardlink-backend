from django.urls import path
from .views import CompleteLandscaperProfileView


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
]
