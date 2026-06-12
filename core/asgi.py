


import os
import django
from django.core.asgi import get_asgi_application
from socketio import ASGIApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from message.socket import sio

django_asgi_app = get_asgi_application()
application = ASGIApp(sio, django_asgi_app)
