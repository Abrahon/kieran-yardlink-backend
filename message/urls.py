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
from .views import (
    MessageCreateView,
    MessageListView,
    MessageUpdateView,
    MessageDeleteView,
)

urlpatterns = [
    # Create a new message
    path("send/messages/", MessageCreateView.as_view(), name="create_message"),

    # Get all messages in a thread (use ?thread=<id>)
    path("messages/list/", MessageListView.as_view(), name="list_messages"),

    # Update a message by ID
    path("messages/<int:pk>/update/", MessageUpdateView.as_view(), name="update_message"),

    # Delete a message by ID
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="delete_message"),
]
