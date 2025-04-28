# your_project/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

import OrderPage.routing # type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_impl.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            OrderPage.routing.websocket_urlpatterns
        )
    ),
})