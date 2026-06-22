from django.urls import path
from .views import (

    ClientServicePreferenceAPIView,
    ClientPreferenceNoteUpdateAPIView,
    ClientJobHistoryAPIView,

    ServiceOverviewAPIView,
    RecentActivityAPIView,

)


urlpatterns = [

    path(
        "client/service-preference/",
        ClientServicePreferenceAPIView.as_view(),
        name="client-service-preference"
    ),
    path(
        "client/service-preference/note/",
        ClientPreferenceNoteUpdateAPIView.as_view(),
        name="client-service-note"
    ),

    path("service-overview/", ServiceOverviewAPIView.as_view()),

    path("activity/recent/", RecentActivityAPIView.as_view(), name="recent-activity"),
]
