# from django.urls import path
# from .views import (
#     CreateOrGetThreadView,
#     ThreadMessagesView,
#     DeleteMessageView,
#     UpdateMessageView
# )

# urlpatterns = [
#     path("thread/create/", CreateOrGetThreadView.as_view(), name="create_or_get_thread"),
#     path("thread/<int:thread_id>/messages/", ThreadMessagesView.as_view(), name="thread_messages"),
#     path("message/<int:message_id>/delete/", DeleteMessageView.as_view(), name="delete_message"),
#     path("message/<int:message_id>/update/", UpdateMessageView.as_view(), name="update_message"),
# ]

from django.urls import path
from .views import ConversationListAPIView,ConversationDetailAPIView,DeleteMultipleConversationsAPIView

urlpatterns = [
    path("conversations/", ConversationListAPIView.as_view(), name="conversation-list"),
    path("conversations/<int:thread_id>/", ConversationDetailAPIView.as_view(), name="conversation-detail"),
       path(
        'conversations/delete/multiple/',
        DeleteMultipleConversationsAPIView.as_view(),
        name='delete-multiple-threads'
    ),

]

