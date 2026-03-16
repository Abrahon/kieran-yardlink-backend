# message/sio_server.py
import os
import django
import socketio
import asyncio
import requests

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Import your models
from message.models import Message

# Async Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio)

# Connect event
@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

# Join room
@sio.event
async def join_room(sid, data):
    room = str(data["room"])
    sio.enter_room(sid, room)
    print(f"Client {sid} joined room {room}")

# Send message
@sio.event
async def send_message(sid, data):
    room = str(data["room"])
    message = data["message"]
    user_id = data["user"]

    # Save message to DB using thread pool
    def save_message():
        return Message.objects.create(
            thread_id=room,
            sender_id=user_id,
            content=message
        )
    preview = {
        "title": f"New message from {sender.get_full_name() or sender.email}",
        "body": text or "Sent a file",
        "thread_id": thread.id
    }

    # ✅ SEND PREVIEW TO ADMIN DASHBOARD
    await sio.emit(
        "notification_preview",
        preview,
        room="admins"
    )

    await asyncio.to_thread(save_message)

    # Broadcast to room
    await sio.emit("receive_message", data, room=room)

# Disconnect
@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)

