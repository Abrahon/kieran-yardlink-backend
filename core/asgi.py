# import os

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import message.routing  # your websocket urls

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             message.routing.websocket_urlpatterns
#         )
#     ),
# })

# import os
# import django
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from django.core.asgi import get_asgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
# django.setup()

# import message.routing   

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             message.routing.websocket_urlpatterns
#         )
#     ),
# })
# core/asgi.py
# Keep default ASGI for Django HTTP only

# import os
# import django
# from django.core.asgi import get_asgi_application
# from socketio import ASGIApp

# # 1️⃣ Set the Django settings module
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
# django.setup()

# # 2️⃣ Import your Socket.IO server from messaging app
# from message.socket import sio  # <-- This is your sio instance

# # 3️⃣ Get the Django ASGI application
# django_asgi_app = get_asgi_application()

# # 4️⃣ Combine Django + Socket.IO
# application = ASGIApp(sio, django_asgi_app)


import os
import django
from django.core.asgi import get_asgi_application
from socketio import ASGIApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from message.socket import sio

django_asgi_app = get_asgi_application()
application = ASGIApp(sio, django_asgi_app)
