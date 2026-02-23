
from django.urls import path
from .views import ConversationListAPIView,ConversationDetailAPIView,DeleteMultipleConversationsAPIView,StartConversationAPIView

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


]

