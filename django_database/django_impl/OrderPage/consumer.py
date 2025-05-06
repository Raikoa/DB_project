# yourapp/consumers.py
import base64
import os
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import osmnx as ox
from django.http import JsonResponse
import requests
from database.models import Order, Restaurant, VideoFrame# type: ignore
from channels.db import database_sync_to_async
import osmnx as ox
from shapely.geometry import Point
from geopy.distance import distance
import networkx as nx
from django.conf import settings
from geopy.distance import geodesic
from threading import Lock
from django.core.files.base import ContentFile
_graph_cache = None
_graph_lock = Lock()

def load_graph_once():
    graph_dir = os.path.join(settings.BASE_DIR, 'osm')
    graph_path = os.path.join(graph_dir, 'taiwan_drive.graphml')
    print(graph_path)
    global _graph_cache
    with _graph_lock:
        if _graph_cache is None:
            if os.path.exists(graph_path):
                print("[INFO] Loading graph from disk...")
                _graph_cache = ox.load_graphml(graph_path)
            else:
                print("[INFO] Graph not found. Downloading...")
                G = ox.graph_from_place("Taiwan", network_type="drive")
                os.makedirs(graph_dir, exist_ok=True)
                ox.save_graphml(G, filepath=graph_path)
                _graph_cache = G
        return _graph_cache
    



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



class OrderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # No receiving logic needed if only sending
        pass

    async def send_order_complete(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))


class DeliveryTracker(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'location.update':
            latitude = data['latitude']
            longitude = data['longitude']
            order_id = data['oid']
            print(f"Received location: {latitude}, {longitude}")
            await self.update_order_location(order_id, latitude, longitude)
            route = await self.get_route(order_id, latitude, longitude)
            print(route)
            if route:
                await self.send(text_data=json.dumps({
                    "type": "route.update",
                    "route": route["real_route"],
                    "fallback_line": route["fallback_line"],
                    "distance": route["distance"],
                    "oid": order_id,
                }))
        if data['type'] == "frameRequest":
            lat = data['latitude']
            lon = data['longitude']
            oid = data['oid']
            framenum = data['FrameNumber']
            print(f"Recieved Frame request: {lat}, {lon}")
            await self.save_frame(oid, lat, lon, framenum)
            print("frame saved")


    @database_sync_to_async
    def update_order_location(self, order_id, lat, lng):
        order = Order.objects.get(id=order_id)
        order.location = f"{lat}:{lng}"
        order.save()

    @database_sync_to_async
    def get_route(self, order_id, lat, lng):
        try:
            
            G = load_graph_once()
            New_G = nx.subgraph(G, max(nx.strongly_connected_components(G), key=len)).copy()
            order = Order.objects.get(id=order_id)
            restaurant = Restaurant.objects.get(Rid=order.restaurant_id)
            rest_coords = (restaurant.latitude, restaurant.longitude)
            delivery_coords = (lat, lng)

            #G = get_graph_near_delivery(delivery_coords, rest_coords, buffer_km=15)
            #graph_path = os.path.join(settings.BASE_DIR, 'osm', 'taiwan_drive.graphml')
            #G = ox.load_graphml(graph_path)
            #print("finished loading path map")
            orig_node = ox.distance.nearest_nodes(New_G, delivery_coords[1], delivery_coords[0])
            dest_node = ox.distance.nearest_nodes(New_G, rest_coords[1], rest_coords[0])
            if not nx.has_path(New_G, orig_node, dest_node):
                print("No path exists between origin and destination")
                return None
            path = nx.shortest_path(New_G, orig_node, dest_node, weight="length")
            route_coords = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path]
            fallback_line = interpolate_line(delivery_coords, rest_coords)
            dist_km = geodesic(delivery_coords, rest_coords).km
            return {
                    "real_route": route_coords,
                    "fallback_line": fallback_line,
                    "distance": dist_km,
                    }
        except Exception as e:
            print(f"[Route Error] {str(e)}")
            return None
        
    @database_sync_to_async
    def save_frame(self, order_id,lat,lng, TimeNum):
        key = "AIzaSyDRPaAyw-McbHYiboHfXCEExlK7zGXrPOg"
        actual_lat, actual_lng = find_nearby_streetview(lat, lng, key)

        if actual_lat is None:
            print(f"No nearby Street View found for {lat}, {lng}")
            return

        location = f"{actual_lat},{actual_lng}"
        heading = 90
        pitch = 0
        fov = 90

        url = f'https://maps.googleapis.com/maps/api/streetview?size=640x640&location={location}&heading={heading}&pitch={pitch}&fov={fov}&key={key}'
        r = requests.get(url)

        if r.status_code == 200:
            file_name = f"{order_id}_streetview_{TimeNum}.jpg"
            image_file = ContentFile(r.content, name=file_name)
            try:
                the_order = Order.objects.get(id=order_id)
                VideoFrame.objects.create(order=the_order, latitude=actual_lat, longitude=actual_lng, frame=image_file)
            except Order.DoesNotExist:
                print(f"Order {order_id} not found.")
        else:
            print(f"Image request failed with status: {r.status_code}")

    async def disconnect(self, close_code):
        pass
    
    

      



def get_graph_near_delivery(delivery_coords, restaurant_coords, buffer_km=5):

    lat_center = (delivery_coords[0] + restaurant_coords[0]) / 2
    lon_center = (delivery_coords[1] + restaurant_coords[1]) / 2

    
    graph = ox.graph_from_point((lat_center, lon_center), dist=buffer_km * 1000, network_type='drive')
    return graph

def interpolate_line(start, end, steps=10):
    lat1, lon1 = start
    lat2, lon2 = end
    return [
        (
            lat1 + (lat2 - lat1) * i / steps,
            lon1 + (lon2 - lon1) * i / steps
        )
        for i in range(steps + 1)
    ]


class MapConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["type"] == "request_map":
            order_id = data["order_id"]
            order = await sync_to_async(Order.objects.get)(id=order_id)
            location = order.location
            if location is None:
                await self.send(text_data=json.dumps({
                "type": "error",
                "message": "No location found for the order."
                }))
                return
            lat, lng = map(str.strip, location.split(":"))
            print(lat, lng) 

            await self.send(text_data=json.dumps({
                    "type": "map",
                    "lat": lat,
                    "lng": lng,
            }))

def find_nearby_streetview(lat, lng, key, step=0.0005, range_steps=1):
    r = requests.get(f'https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lng}&key={key}')
    if r.status_code == 200 and r.json().get("status") == "OK":
        return lat, lng
    offsets = [-step * i for i in range(1, range_steps + 1)] + [0] + [step * i for i in range(1, range_steps + 1)]
    for lat_offset in offsets:
        for lng_offset in offsets:
            trial_lat = lat + lat_offset
            trial_lng = lng + lng_offset
            location = f"{trial_lat},{trial_lng}"

            meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={location}&key={key}"
            response = requests.get(meta_url)
            if response.status_code == 200 and response.json().get("status") == "OK":
                return trial_lat, trial_lng  # ✅ found a valid spot
    return None, None  # ❌ no image found nearby