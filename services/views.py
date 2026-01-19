

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Service, ClientServicePreference
from profiles.models import ClientProfile
from rest_framework.views import APIView
from django.utils.timezone import now  
from services.serializers import ClientServicePreferenceReadSerializer
from bookings.models import ServiceBooking, BookingStatus
from rest_framework.exceptions import NotFound

from .serializers import (
    ServiceSerializer,
    ClientServicePreferenceWriteSerializer,
    ClientServicePreferenceReadSerializer
)

# ---------------- Standard Service List ----------------
class StandardServiceListAPIView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Service.objects.filter(is_standard=True)


# ---------------- Add Standard Service (Admin Only) ----------------
class StandardServiceCreateAPIView(generics.CreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminUser]  # use IsAdminUser in real project

    def perform_create(self, serializer):
        serializer.save(is_standard=True, landscaper=None)


# ---------------- Add Custom Service (Landscaper) ----------------
class CustomServiceCreateAPIView(generics.CreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        landscaper = self.request.user.landscaper_profile
        serializer.save(is_standard=False, landscaper=landscaper)

# ---------------- Client Preference View ----------------

class ClientServicePreferenceAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            client = ClientProfile.objects.get(user=self.request.user)
        except ClientProfile.DoesNotExist:
            raise NotFound(detail="Client profile does not exist for this user.")

        preference, _ = ClientServicePreference.objects.get_or_create(client=client)
        return preference

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ClientServicePreferenceReadSerializer
  
        return ClientServicePreferenceWriteSerializer

# ---------------- Client Service Overview ----------------
# class ClientServiceOverviewAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         client = ClientProfile.objects.get(user=request.user)
#         preference, _ = ClientServicePreference.objects.get_or_create(client=client)
#         serializer = ClientServicePreferenceReadSerializer(preference)

#         return Response({
#             "service_overview": serializer.data,
#             "next_schedule": {
#                 "day": "Saturday",
#                 "time": "10:00 AM"
#             },
#             "previous_job": {
#                 "status": "completed",
#                 "total": serializer.data["total_price"]
#             },
#             "payment_status": "pending"
#         })



class ClientServiceOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client_profile = request.user.clientprofile
        except AttributeError:  # in case clientprofile does not exist
            raise NotFound("Client profile does not exist for this user.")

        preference, _ = ClientServicePreference.objects.get_or_create(client=client_profile)
        serializer = ClientServicePreferenceReadSerializer(preference)

        # Next scheduled booking
        next_booking = (
            ServiceBooking.objects
            .filter(
                client=request.user,
                status__in=[
                    BookingStatus.REQUESTED,
                    BookingStatus.ACCEPTED,
                    BookingStatus.IN_PROGRESS
                ],
                scheduled_date__gte=now().date()  # <- fixed here
            )
            .order_by("scheduled_date")
            .first()
        )

        # Last completed booking
        previous_booking = (
            ServiceBooking.objects
            .filter(client=request.user, status=BookingStatus.COMPLETED)
            .order_by("-completed_at")
            .first()
        )

        return Response({
            "service_overview": serializer.data,
            "next_schedule": {
                "date": next_booking.scheduled_date if next_booking else None,
                "time": next_booking.scheduled_date if next_booking else None
            },
            "previous_job": {
                "status": previous_booking.status if previous_booking else None,
                "total": previous_booking.agreed_price if previous_booking else "0.00"
            },
            "payment_status": (
                "paid" if previous_booking and previous_booking.status == BookingStatus.COMPLETED
                else "pending"
            )
        })



from rest_framework.exceptions import NotFound
from .serializers import ClientServicePreferenceReadSerializer
from .models import ClientServicePreference

class ClientPreferenceNoteUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            client = request.user.clientprofile
        except AttributeError:
            raise NotFound("Client profile does not exist.")

        preference, _ = ClientServicePreference.objects.get_or_create(client=client)
        note = request.data.get("note", "")
        preference.note = note
        preference.save(update_fields=["note"])

        serializer = ClientServicePreferenceReadSerializer(preference)
        return Response(serializer.data)
