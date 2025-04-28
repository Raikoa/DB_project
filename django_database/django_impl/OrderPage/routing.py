# your_project/routing.py
from django.urls import re_path
from OrderPage import consumer # type: ignore

websocket_urlpatterns = [
    re_path(r'ws/orders/$', consumer.OrderConsumer.as_asgi()),
]