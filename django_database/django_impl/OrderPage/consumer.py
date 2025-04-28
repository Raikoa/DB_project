# yourapp/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("orders", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("orders", self.channel_name)

    async def receive(self, text_data):
        # usually unused here unless client sends something
        pass

    async def order_update(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))
