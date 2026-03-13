# # bookings/urls.py
# from django.urls import path
# from .views import ServiceBookingRescheduleAPIView

# urlpatterns = [
#     path("bookings/<int:booking_id>/reschedule/", ServiceBookingRescheduleAPIView.as_view()),
# ]

from django.urls import path
from .views import (
    ClientBookingListView,
    BookingRequestRetrieveDestroyView,
    client_confirm_booking,
    LandscaperBookingListView,
    landscaper_accept_booking,
)

urlpatterns = [
    # Client
    path("bookings/", ClientBookingListView.as_view(), name="client-booking-list-create"),
    path("bookings/<int:pk>/", BookingRequestRetrieveDestroyView.as_view(), name="client-booking-detail"),
    path("bookings/<int:pk>/confirm/", client_confirm_booking, name="client-booking-confirm"),

    # Landscaper
    path("landscaper/bookings/pending/", LandscaperBookingListView.as_view(), name="landscaper-pending-bookings"),
    path("landscaper/bookings/<int:pk>/accept/", landscaper_accept_booking, name="landscaper-accept-booking"),
]