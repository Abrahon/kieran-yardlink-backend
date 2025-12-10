from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Message
from .serializers import MessageSerializer

# Only authenticated users can create, update, or delete messages
class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)  # Automatically set sender

# Get all messages for a thread
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread_id = self.request.query_params.get('thread')
        if not thread_id:
            raise ValidationError({"thread": "Thread ID is required"})
        return Message.objects.filter(thread_id=thread_id).order_by("created_at")

# Update a message (only sender can update)
class MessageUpdateView(generics.UpdateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        message = self.get_object()
        if message.sender != self.request.user:
            raise ValidationError({"detail": "You cannot update someone else's message"})
        serializer.save()

# Delete a message (only sender can delete)
class MessageDeleteView(generics.DestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            raise ValidationError({"detail": "You cannot delete someone else's message"})
        instance.delete()
