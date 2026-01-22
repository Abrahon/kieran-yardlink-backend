# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from .models import ChatThread, Message
# from django.db.models import Q  # <- add this import

# class ConversationListAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         threads = ChatThread.objects.filter(
#             Q(client=user) | Q(landscaper=user)  # <- use Q directly, not models.Q
#         ).order_by('-updated_at')

#         data = []
#         for thread in threads:
#             other = thread.landscaper if thread.client == user else thread.client
#             last_message = thread.messages.order_by('-created_at').first()
#             data.append({
#                 "thread_id": thread.id,
#                 "with_user_id": other.id,
#                 "with_user_name": other.get_full_name() or other.email,
#                 "last_message": last_message.text if last_message else None,
#                 "last_message_time": last_message.created_at.isoformat() if last_message else None,
#             })

#        return Response(data)

# class ConversationDetailAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, thread_id):
#         try:
#             thread = ChatThread.objects.get(id=thread_id)
#         except ChatThread.DoesNotExist:
#             return Response({"error": "Thread not found"}, status=404)

#         if request.user not in [thread.client, thread.landscaper]:
#             return Response({"error": "Not allowed"}, status=403)

#         messages = thread.messages.order_by('created_at')
#         data = []

#         for msg in messages:
#             data.append({
#                 "id": msg.id,
#                 "sender_id": msg.sender.id,
#                 "sender_name": msg.sender.get_full_name() or msg.sender.email,
#                 "text": msg.text,
#                 "file_url": msg.file.url if msg.file else None,
#                 "seen_at": msg.seen_at.isoformat() if msg.seen_at else None,
#                 "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
#                 "created_at": msg.created_at.isoformat(),
#             })  # ✅ both } and ) are closed

#         return Response({
#             "thread_id": thread.id,
#             "messages": data
#         })


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.views import APIView
from .models import ChatThread, Message


class ConversationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        threads = ChatThread.objects.filter(
            Q(client=user) | Q(landscaper=user)
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
                "file_url": msg.file.url if msg.file else None,
                "seen_at": msg.seen_at.isoformat() if msg.seen_at else None,
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "created_at": msg.created_at.isoformat(),
            })

        return Response({
            "thread_id": thread.id,
            "messages": data
        })
#  delete user who is send message

class DeleteThreadFromInboxAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, thread_id):
        """
        "Delete" a thread from the inbox of the requesting user.
        This just hides the thread for this user.
        """
        try:
            thread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            return Response({"detail": "Thread not found."}, status=404)

        if request.user not in thread.participants:
            return Response({"detail": "Not allowed."}, status=403)

        # Hide the thread for this user
        thread.hidden_for.add(request.user)
        return Response({"detail": "Thread removed from your inbox."}, status=200)
