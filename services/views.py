from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Service
from .serializers import ServiceSerializer
from common.permissions import IsLandscaper,IsClient
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import ClientServicePreference
from .serializers import ClientServicePreferenceSerializer
from profiles.models import ClientProfile


class ServiceListCreateView(generics.ListCreateAPIView):
    """
    GET  -> List own services
    POST -> Create a service
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get_queryset(self):
        return Service.objects.filter(
            landscaper=self.request.user.landscaper_profile
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    -> Retrieve
    PUT    -> Update
    PATCH  -> Partial update
    DELETE -> Delete
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated, IsLandscaper]

    def get_queryset(self):
        return Service.objects.filter(
            landscaper=self.request.user.landscaper_profile
        )


# client views 

class ClientServicePreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientServicePreferenceSerializer
    permission_classes = [IsAuthenticated, IsClient]

    def get_object(self):
        client = ClientProfile.objects.get(user=self.request.user)
        preference, _ = ClientServicePreference.objects.get_or_create(
            client=client
        )
        return preference
