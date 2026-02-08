from django.urls import path
from .views import CompleteLandscaperProfileView,GetLandscaperProfileView,LandscaperFind,WorkingHoursListCreateView,CreateServiceView,ListServicesView,UpdateLandscaperProfileView,UpdateServiceView


urlpatterns = [
    path("landscaper/complete-profile/",CompleteLandscaperProfileView.as_view()),
    path(
        "landscaper/profile/update/",
        UpdateLandscaperProfileView.as_view(),
        name="landscaper-profile-update"
    ),
    path("landscaper/profile/", GetLandscaperProfileView.as_view(), name="get-landscaper-profile"),
    path("service/create/", CreateServiceView.as_view(), name="create-service"),
    path("services/", ListServicesView.as_view(), name="list-services"),
    path("landscapers/search/", LandscaperFind.as_view(), name="landscaper-search"),
    path('working-hours/', WorkingHoursListCreateView.as_view(), name='working-hours'),
    path("services/update/<int:id>/", UpdateServiceView.as_view()), 
]
