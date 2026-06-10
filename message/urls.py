
from django.urls import path
from .views import AdminChatThreadListView, ConversationListAPIView,ConversationDetailAPIView,DeleteMultipleConversationsAPIView, MessageCreateView,StartConversationAPIView,AdminTagConversationAPIView,AdminConversationListAPIView,AdminConversationDetailAPIView

urlpatterns = [
    path("conversations/", ConversationListAPIView.as_view(), name="conversation-list"),
    path("conversations/<int:thread_id>/", ConversationDetailAPIView.as_view(), name="conversation-detail"),
    path(
        'conversations/delete/multiple/',
        DeleteMultipleConversationsAPIView.as_view(),
        name='delete-multiple-threads'
    ),
    path( 
        "chat/start/<int:user_id>/",
        StartConversationAPIView.as_view(),
        name="start-conversation"
    ),
    path(
        "conversations/<int:thread_id>/tag/",
        AdminTagConversationAPIView.as_view(),
        name="tag-conversation"
    ),
    
    path("admin/conversations/", AdminConversationListAPIView.as_view(), name="admin-conversation-list"),
    path("admin/conversations/<int:thread_id>/", AdminConversationDetailAPIView.as_view(), name="admin-conversation-detail"),

        # Send Message + Auto Tag
    path(
        "messages/send/",
        MessageCreateView.as_view(),
        name="send-message",
    ),

    # Admin Chat Thread List + Filter
    path(
        "admin/chat-threads/",
        AdminChatThreadListView.as_view(),
        name="admin-chat-threads",
    ),

]

