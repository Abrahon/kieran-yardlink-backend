import logging
import socketio
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from channels.db import database_sync_to_async
from .models import ChatThread, Message
from django.utils import timezone
  

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
    await sio.enter_room(sid, str(user.id)) 

    # ✅ Admin monitoring room
    if user.is_staff:
        await sio.enter_room(sid, "admins")

    full_name = user.get_full_name().strip() or user.email
    logger.info(f"Connected: {full_name} ({user.id}) - SID {sid}")
    return True


# send message
# @sio.event
@sio.event
async def send_message(sid, data):
    user_id = connected_users.get(sid)
    if not user_id:
        return

    receiver_id = data.get('to_user')
    text = (data.get('message') or '').strip()

    # file_url is ONLY for frontend display (already uploaded via REST)
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

    # ✅ SAVE MESSAGE (TEXT ONLY)
    message = await save_message(
        thread=thread,
        sender=sender,
        text=text
        #  DO NOT pass file_url here
    )

    payload = {
        "id": message.id,
        "thread_id": thread.id,
        "sender_id": str(sender.id),
        "sender_name": sender.get_full_name() or sender.email,
        "text": message.text,
        "file_url": file_url,  #  frontend-only reference
        "created_at": message.created_at.isoformat(),
        "is_me": True
    }

    # --- send to receiver ---
    receiver_sid = user_sockets.get(str(receiver.id))
    if receiver_sid:
        await sio.emit('new_message', payload, to=receiver_sid)

        await sio.emit(
            'notification',
            {
                "title": f"New message from {sender.get_full_name() or sender.email}",
                "body": message.text or "Sent a file",
                "thread_id": thread.id,
                "sender_id": str(sender.id),
            },
            to=receiver_sid
        )

    # --- confirmation to sender ---
    await sio.emit('message_sent', payload, to=sid)

@sio.event
async def disconnect(sid):
    user_id = connected_users.pop(sid, None)
    if user_id and user_sockets.get(user_id) == sid:
        user_sockets.pop(user_id)
    logger.info(f"Disconnected: {user_id}")


@sio.event
async def update_message(sid, data):
    message_id = data.get("message_id")
    new_text = data.get("text")

    user_id = connected_users.get(sid)

    @database_sync_to_async
    def update():
        msg = Message.objects.get(id=message_id, sender_id=user_id)
        msg.text = new_text
        msg.save(update_fields=["text"])

    await update()

    await sio.emit(
        "message_updated",
        {"message_id": message_id, "text": new_text},
        room=f"thread_{data.get('thread_id')}"
    )

# delete
@sio.event
async def delete_message(sid, data):
    message_id = data.get("message_id")
    for_all = data.get("for_all", False)

    user_id = connected_users.get(sid)

    @database_sync_to_async
    def delete():
        msg = Message.objects.get(id=message_id)
        user = User.objects.get(id=user_id)

        if for_all and msg.sender_id == user.id:
            msg.is_deleted_for_all = True
            msg.text = ""
            msg.file = None
            msg.save()
        else:
            msg.deleted_for.add(user)

    await delete()

    await sio.emit(
        "message_deleted",
        {"message_id": message_id, "for_all": for_all},
        room=f"thread_{data.get('thread_id')}"
    )


# seen message
@sio.event
async def message_seen(sid, data):
    message_id = data.get("message_id")
    thread_id = data.get("thread_id")

    @database_sync_to_async
    def mark_seen():
        Message.objects.filter(
            id=message_id,
            seen_at__isnull=True
        ).update(seen_at=timezone.now())

    await mark_seen()

    await sio.emit(
        "message_seen",
        {"message_id": message_id},
        room=f"thread_{thread_id}"
    )

# delivered
@sio.event
async def message_delivered(sid, data):
    message_id = data.get("message_id")

    @database_sync_to_async
    def mark_delivered():
        Message.objects.filter(
            id=message_id,
            delivered_at__isnull=True
        ).update(delivered_at=timezone.now())

    await mark_delivered()

# typing
@sio.event
async def typing(sid, data):
    thread_id = data.get("thread_id")
    user = await get_user_by_id(connected_users.get(sid))
    await sio.emit("typing", {"user_id": str(user.id), "thread_id": thread_id}, room=f"thread_{thread_id}")

@sio.event
async def disconnect(sid):
    user_id = connected_users.pop(sid, None)
    if user_id and user_sockets.get(user_id) == sid:
        user_sockets.pop(user_id)
    logger.info(f"Disconnected: {user_id}")



async def send_admin_message(
    thread,
    receiver,
    message
):

    payload = {
        "id": message.id,
        "thread_id": thread.id,
        "sender_name": "YardLink Support",
        "text": message.text,
        "is_admin": True,
        "created_at": message.created_at.isoformat()
    }

    receiver_sid = user_sockets.get(
        str(receiver.id)
    )

    if receiver_sid:

        await sio.emit(
            "new_message",
            payload,
            to=receiver_sid
        )