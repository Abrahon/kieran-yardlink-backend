from rest_framework import generics, permissions
from .models import Plan
from .serializers import PlanSerializer


class IsAdmin(permissions.BasePermission):
    """Allow only admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"
    

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [permissions.AllowAny()]


class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdmin()]
        return [permissions.AllowAny()]
