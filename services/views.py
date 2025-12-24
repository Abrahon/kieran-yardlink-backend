from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Service
from .serializers import ServiceSerializer
from .permissions import IsLandscaper


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
