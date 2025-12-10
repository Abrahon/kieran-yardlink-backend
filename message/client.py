import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("Connected!")
    sio.emit("join_room", {"room": "2"})
    sio.emit("send_message", {"room": "2", "user": 1, "message": "Hello world!"})

@sio.event
def receive_message(data):
    print("New message:", data)

sio.connect("http://127.0.0.1:8000")
sio.wait()
