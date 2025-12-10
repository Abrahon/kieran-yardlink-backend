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
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_asgi_application()
