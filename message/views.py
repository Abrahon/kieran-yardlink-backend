
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from message.serializers import ChatThreadSerializer, MessageSerializer
from .models import ChatThread, Message
from accounts.models import User
from django.db.models.functions import Lower, Trim
from rest_framework import status
from .models import ChatThread
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ChatThread, Message
from rest_framework.permissions import IsAdminUser


class ConversationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        threads = ChatThread.objects.filter(
            Q(client=user) | Q(landscaper=user)
        ).order_by('-updated_at')

        data = []

        for thread in threads:
            other_user = thread.landscaper if thread.client == user else thread.client

            # Image from profile if exists
            image = None
            if hasattr(other_user, "landscaperprofilies"):
                image = other_user.landscaperprofilies.image.url if other_user.landscaperprofilies.image else None
            elif hasattr(other_user, "clientprofile"):
                image = other_user.clientprofile.image.url if other_user.clientprofile.image else None

            # Address: get directly from User model if exists
            address = getattr(other_user, "address", None)

            last_message = thread.messages.order_by('-created_at').first()

            data.append({
                "thread_id": thread.id,
                "with_user_id": other_user.id,
                "with_user_name": getattr(other_user, "name", "") or other_user.email,
                "email": other_user.email,
                "image": image,
                "address": address,
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





class DeleteMultipleConversationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        thread_ids = request.data.get("thread_ids")

        if not thread_ids or not isinstance(thread_ids, list):
            return Response(
                {"detail": "thread_ids must be a list of IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        threads = ChatThread.objects.filter(
            Q(client=request.user) | Q(landscaper=request.user),
            id__in=thread_ids
        )

        messages = Message.objects.filter(thread__in=threads)

        for message in messages:
            message.deleted_for.add(request.user)

        # Optional: exclude deleted messages when returning updated threads
        remaining_threads = ChatThread.objects.filter(
            Q(client=request.user) | Q(landscaper=request.user)
        ).exclude(messages__deleted_for=request.user).distinct()

        return Response(
            {
                "detail": "Selected conversations removed from your inbox.",
                "remaining_threads_count": remaining_threads.count()
            },
            status=status.HTTP_200_OK
        )



#coversation
class StartConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        current_user = request.user

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if current_user == other_user:
            return Response(
                {"error": "You cannot start conversation with yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check existing thread (both directions)
        thread = ChatThread.objects.filter(
            Q(client=current_user, landscaper=other_user) |
            Q(client=other_user, landscaper=current_user)
        ).first()

        if not thread:
            thread = ChatThread.objects.create(
                client=current_user if current_user.role == "client" else other_user,
                landscaper=current_user if current_user.role == "landscaper" else other_user
            )

        return Response({
            "thread_id": thread.id,
            "client_id": thread.client.id,
            "landscaper_id": thread.landscaper.id,
        }, status=status.HTTP_200_OK)



class AdminTagConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        if not request.user.is_staff:
            return Response({"error": "Admin only"}, status=403)

        tag = (request.data.get("tag") or "").strip()

        if not tag:
            return Response(
                {"error": "Tag is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            thread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            return Response({"error": "Thread not found"}, status=404)

        thread.tag = tag
        thread.save(update_fields=["tag"])

        return Response({
            "message": "Conversation tagged",
            "thread_id": thread.id,
            "tag": thread.tag
        })
    

# admin
class AdminConversationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Admin only"},
                status=status.HTTP_403_FORBIDDEN
            )

        search = request.GET.get("search", "").strip()
        tag = request.GET.get("tag", "").strip()

        threads = ChatThread.objects.select_related(
            "client", "landscaper"
        ).prefetch_related("messages").order_by("-updated_at")

        if search:
            threads = threads.filter(
                Q(client__name__icontains=search) |
                Q(client__email__icontains=search) |
                Q(landscaper__name__icontains=search) |
                Q(landscaper__email__icontains=search)
            )

        if tag:
            normalized_tag = tag.strip().lower()

            threads = threads.annotate(
                normalized_db_tag=Lower(Trim("tag"))
            ).filter(
                normalized_db_tag=normalized_tag
            )

        data = []

        for thread in threads:
            messages = thread.messages.select_related("sender").order_by("created_at")

            message_list = [
                {
                    "id": msg.id,
                    "sender_id": msg.sender.id if msg.sender else None,
                    "sender_name": msg.sender.get_full_name() or msg.sender.email if msg.sender else "Unknown",
                    "text": msg.text,
                    "file_url": msg.file.url if msg.file else None,
                    "message_type": msg.message_type,
                    "seen_at": msg.seen_at,
                    "delivered_at": msg.delivered_at,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ]

            last_message = messages.last()

            data.append({
                "thread_id": thread.id,
                "client": {
                    "id": thread.client.id,
                    "name": getattr(thread.client, "name", "") or thread.client.email,
                    "email": thread.client.email,
                    "role": getattr(thread.client, "role", ""),
                },
                "landscaper": {
                    "id": thread.landscaper.id,
                    "name": getattr(thread.landscaper, "name", "") or thread.landscaper.email,
                    "email": thread.landscaper.email,
                    "role": getattr(thread.landscaper, "role", ""),
                },
                "tag": thread.tag,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,

                # ALL messages
                "messages": message_list,

                # last message
                "last_message": {
                    "id": last_message.id,
                    "sender_id": last_message.sender.id if last_message.sender else None,
                    "sender_name": last_message.sender.get_full_name() or last_message.sender.email if last_message.sender else "Unknown",
                    "text": last_message.text,
                    "file_url": last_message.file.url if last_message.file else None,
                    "created_at": last_message.created_at,
                } if last_message else None,

                "messages_count": len(message_list),
            })

        return Response({
            "count": len(data),
            "results": data
        })

# old
class AdminConversationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        if not request.user.is_staff:
            return Response(
                {"error": "Admin only"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            thread = ChatThread.objects.select_related(
                "client",
                "landscaper"
            ).get(id=thread_id)
        except ChatThread.DoesNotExist:
            return Response(
                {"error": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        messages = thread.messages.select_related("sender").order_by("created_at")

        message_data = []
        for msg in messages:
            message_data.append({
                "id": msg.id,
                "sender_id": msg.sender.id,
                "sender_name": msg.sender.get_full_name() or msg.sender.email,
                "text": msg.text,
                "file_url": msg.file.url if msg.file else None,
                "message_type": msg.message_type,
                "seen_at": msg.seen_at.isoformat() if msg.seen_at else None,
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "is_deleted_for_all": msg.is_deleted_for_all,
                "created_at": msg.created_at.isoformat(),
            })

        return Response(
            {
                "thread_id": thread.id,
                "tag": thread.tag,
                "client": {
                    "id": thread.client.id,
                    "name": getattr(thread.client, "name", "") or thread.client.email,
                    "email": thread.client.email,
                    "role": getattr(thread.client, "role", ""),
                },
                "landscaper": {
                    "id": thread.landscaper.id,
                    "name": getattr(thread.landscaper, "name", "") or thread.landscaper.email,
                    "email": thread.landscaper.email,
                    "role": getattr(thread.landscaper, "role", ""),
                },
                "messages_count": len(message_data),
                "messages": message_data,
            },
            status=status.HTTP_200_OK
        )
    
    
# old
class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        thread_id = request.data.get("thread_id")
        text = request.data.get("text", "").lower()

        thread = ChatThread.objects.get(id=thread_id)

        # -------------------------
        # CREATE MESSAGE
        # -------------------------
        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            text=request.data.get("text"),
            file=request.data.get("file")
        )

        # -------------------------
        # AUTO TAG LOGIC (NO AI)
        # -------------------------
        if any(w in text for w in ["payment", "invoice", "bill"]):
            thread.tag = "billing"

        elif any(w in text for w in ["subscribe", "plan", "subscription"]):
            thread.tag = "subscription"

        elif any(w in text for w in ["help", "issue", "problem"]):
            thread.tag = "support"

        elif any(w in text for w in ["price", "quote", "cost"]):
            thread.tag = "inquiry"

        else:
            thread.tag = "general"

        thread.save()

        return Response({
            "message": "Message sent",
            "tag": thread.tag
        })


class AdminChatThreadListView(generics.ListAPIView):
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = ChatThread.objects.all()

        tag = self.request.query_params.get("tag")

        if tag:
            queryset = queryset.filter(tag=tag)

        return queryset.order_by("-updated_at")



class AdminReplyAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, thread_id):

        thread = ChatThread.objects.filter(
            id=thread_id
        ).first()

        if not thread:
            return Response(
                {"detail": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        text = request.data.get("text")

        if not text:
            return Response(
                {"detail": "Message required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = Message.objects.create(
            thread=thread,
            sender=request.user,
            text=text,
            is_admin_message=True
        )

        return Response({
            "id": message.id,
            "message": message.text,
            "created_at": message.created_at
        })