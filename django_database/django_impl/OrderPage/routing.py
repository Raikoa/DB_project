# your_project/routing.py
from django.urls import re_path
from OrderPage import consumer # type: ignore

websocket_urlpatterns = [
    re_path(r'ws/orders/$', consumer.OrderConsumer.as_asgi()),
    re_path(r'ws/notify/(?P<user_id>\d+)/$', consumer.OrderNotificationConsumer.as_asgi()),
    re_path(r'ws/delivery/$', consumer.DeliveryTracker.as_asgi()),
    re_path(r'ws/map/$', consumer.MapConsumer.as_asgi()),
]