from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatThread, Message
from django.db.models import Q  # <- add this import

class ConversationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        threads = ChatThread.objects.filter(
            Q(client=user) | Q(landscaper=user)  # <- use Q directly, not models.Q
        ).order_by('-updated_at')

        data = []
        for thread in threads:
            other = thread.landscaper if thread.client == user else thread.client
            last_message = thread.messages.order_by('-created_at').first()
            data.append({
                "thread_id": thread.id,
                "with_user_id": other.id,
                "with_user_name": other.get_full_name() or other.email,
                "last_message": last_message.text if last_message else None,
                "last_message_time": last_message.created_at.isoformat() if last_message else None,
            })

        return Response(data)


class ConversationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        try:
            thread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            return Response({"error": "Thread not found"}, status=404)

        # Check if user is part of thread
        if request.user not in [thread.client, thread.landscaper]:
            return Response({"error": "Not allowed"}, status=403)

        messages = thread.messages.order_by('created_at')
        data = []
        for msg in messages:
            data.append({
                "id": msg.id,
                "sender_id": msg.sender.id,
                "sender_name": msg.sender.get_full_name() or msg.sender.email,
                "text": msg.text,
                "file_url": getattr(msg, 'file', None),
                "seen_at": msg.seen_at.isoformat() if msg.seen_at else None,
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "created_at": msg.created_at.isoformat(),
            })

        return Response({"thread_id": thread.id, "messages": data})
