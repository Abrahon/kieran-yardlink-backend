import logging
import socketio
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from channels.db import database_sync_to_async
from .models import ChatThread, Message

logger = logging.getLogger(__name__)
User = get_user_model()

# -----------------------------
# Socket.IO server
# -----------------------------
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# Track connections
connected_users = {}  # sid -> user_id
user_sockets = {}     # user_id -> sid

# -----------------------------
# Database helpers
# -----------------------------
@database_sync_to_async
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)

@database_sync_to_async
def get_thread(sender, receiver):
    """Return existing thread between two users."""
    return ChatThread.objects.filter(
        client=sender, landscaper=receiver
    ).first() or ChatThread.objects.filter(
        client=receiver, landscaper=sender
    ).first()

@database_sync_to_async
def create_thread(sender, receiver):
    """Create a new chat thread."""
    return ChatThread.objects.create(client=sender, landscaper=receiver)

@database_sync_to_async
def save_message(thread, sender, text=None, file_url=None):
    """Save message with optional file."""
    message = Message.objects.create(
        thread=thread,
        sender=sender,
        text=text or ""
    )
    if file_url:
        message.file = file_url
        message.save(update_fields=['file'])
    return message

# -----------------------------
# Socket.IO events
# -----------------------------
@sio.event
async def connect(sid, environ, auth):
    token = auth.get('token') if auth else None
    if not token:
        logger.warning(f"Connection rejected: No token - SID {sid}")
        return False

    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = UntypedToken(token)
        user_id = int(payload['user_id'])
        user = await get_user_by_id(user_id)
    except Exception as e:
        logger.warning(f"Connection rejected: Invalid token - {e}")
        return False

    connected_users[sid] = str(user.id)
    user_sockets[str(user.id)] = sid
    await sio.save_session(sid, {'user': user})
    await sio.enter_room(sid, str(user.id))  # personal room

    full_name = user.get_full_name().strip() or user.email
    logger.info(f"Connected: {full_name} ({user.id}) - SID {sid}")
    return True

@sio.event
async def send_message(sid, data):
    user_id = connected_users.get(sid)
    if not user_id:
        return

    receiver_id = data.get('to_user')
    text = data.get('message', '').strip()
    file_url = data.get('file_url')

    if not receiver_id or (not text and not file_url):
        await sio.emit('error', {'error': 'Invalid data'}, to=sid)
        return

    try:
        sender = await get_user_by_id(user_id)
        receiver = await get_user_by_id(int(receiver_id))
    except Exception:
        await sio.emit('error', {'error': 'User not found'}, to=sid)
        return

    # Find or create thread
    thread = await get_thread(sender, receiver)
    if not thread:
        thread = await create_thread(sender, receiver)

    # Save message
    message = await save_message(thread, sender, text, file_url)

    payload = {
        "id": message.id,
        "thread_id": thread.id,
        "sender_id": str(sender.id),
        "sender_name": sender.get_full_name() or sender.email,
        "text": message.text,
        "file_url": getattr(message, 'file', None),
        "created_at": message.created_at.isoformat(),
        "is_me": True
    }

    # --- SEND TO RECEIVER ---
    receiver_sid = user_sockets.get(str(receiver.id))
    if receiver_sid:
        await sio.emit('new_message', payload, to=receiver_sid)

    # --- SEND CONFIRMATION TO SENDER ---
    await sio.emit('message_sent', payload, to=sid)

@sio.event
async def disconnect(sid):
    user_id = connected_users.pop(sid, None)
    if user_id and user_sockets.get(user_id) == sid:
        user_sockets.pop(user_id)
    logger.info(f"Disconnected: {user_id}")
