# yourapp/consumers.py
import asyncio
import base64
import heapq
from itertools import count
import math
import os
import pickle
import re
import threading
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import joblib
import numpy as np
import osmnx as ox
from django.http import JsonResponse
from osmnx import features
import pandas as pd
import requests
from database.models import Order, Restaurant# type: ignore
from channels.db import database_sync_to_async
import osmnx as ox
from shapely.geometry import LineString, Point
from geopy.distance import distance
import networkx as nx
from django.conf import settings
from geopy.distance import geodesic
from threading import Lock
from django.core.files.base import ContentFile
from math import sqrt
from sklearn.preprocessing import StandardScaler
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
semaphore = asyncio.Semaphore(20)
executor = ThreadPoolExecutor(max_workers=8)
_graph_cache = None
_graph_lock = threading.Lock()
_graph_loaded = threading.Event()
road_semaphore = asyncio.Semaphore(2)
center_df = pd.read_xml('data/1050812_行政區經緯度(toPost).xml')
center_df = center_df.rename(columns={
    "行政區名": "district_name",
    "中心點經度": "center_lng",
    "中心點緯度": "center_lat"
})
area_df = pd.read_csv("data/Area_sizes.csv")
land = gpd.read_file("data/ne_50m_land/ne_50m_land.shp")
OFFSET_DEGREES = 0.00225  # ~250m in degrees (varies slightly by latitude)
def load_graph_once():
    global _graph_cache

    # Fast path: if already loaded, no locking needed
    if _graph_cache is not None:
        print("[INFO] Loading graph from cache (gpickle)...")
        return _graph_cache

    # If another thread is already loading the graph, wait until it's done
    if _graph_loaded.is_set():
        print("[INFO] Loading graph from cahce (gpickle)...")
        return _graph_cache

    with _graph_lock:
        # Check again after acquiring the lock (double-checked locking)
        if _graph_cache is not None:
            return _graph_cache

        graph_dir = os.path.join(settings.BASE_DIR, 'osm')
        gpickle_path = os.path.join(graph_dir, 'taiwan_drive.gpickle')

        if os.path.exists(gpickle_path):
            print("[INFO] Loading graph from disk (gpickle)...")
            with open(gpickle_path, "rb") as f:
                _graph_cache = pickle.load(f)
        else:
            print("[INFO] GPickle not found. Downloading from OSM and saving...")
            G = ox.graph_from_place("Taiwan", network_type="drive")
            os.makedirs(graph_dir, exist_ok=True)
            with open(gpickle_path, "wb") as f:
                pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
            _graph_cache = G

        _graph_loaded.set()  # Signal all waiting threads
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
        self.flag = 0
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("in tracker")
        if data['type'] == 'location.update':
            print("in route")
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
                    "static_route": route["static_route"],
                    "fallback_line": route["fallback_line"],
                    "distance": route["distance"],
                    "oid": order_id,
                }))
                # if self.flag == 0:
                #     heatmap = await self.compute_heatmap(route)
                #     await self.send(text_data=json.dumps({
                #         "type": "heatmap_data",
                #         "heatmap": heatmap,
                #     }))
                #     self.flag = 1

                '''
                full_route = route["real_route"] + route["static_route"][1:]
                sampled_route = sample_route(full_route, step=5)
                key = "3f6724b1303b0cc404e1b0608533662d"
                tomtomKey = "pz0l27KTUL4Vsu5jSlZ91Wt9yzcYqIRf"
                results = []
                for lat, lng in sampled_route:
                    # Traffic
                    traffic_data = get_traffic_data_point(lat, lng, tomtomKey)
                    congestion = traffic_data["congestion"] if traffic_data else None

                    # Elevation
                    elevation = get_elevation_point(lat, lng)

                    # Road complexity
                    road_score = compute_road_complexity_point(lat, lng)

                    # Weather
                    weather_data = get_weather_data_point(lat, lng, key)
                    weather_score = compute_weather_score_point(weather_data) if weather_data else None

                    # Building complexity
                    building_score = compute_building_complexity_point(lat, lng)

                    results.append({
                        "lat": lat,
                        "lng": lng,
                        "congestion": congestion,
                        "elevation": elevation,
                        "road_complexity": road_score,
                        "weather_score": weather_score,
                        "building_score": building_score,
                    })
                heatmap = []
                for i in results:
                    intensity = np.mean([
                        normalize(i["congestion"]),
                        normalize(i["elevation"]),
                        normalize(i["road_complexity"]),
                        normalize(i["weather_score"]),
                        normalize(i["building_score"]),
                    ])
                    heatmap.append({
                        "lat": i["lat"],
                        "lng": i["lng"],
                        "score": intensity,
                    })
                await self.send(text_data=json.dumps({
                    "type": "heatmap_data",
                    "heatmap": heatmap,
                }))
                '''
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

    async def compute_heatmap(self, route):
        print("🔧 Computing heatmap...")
        
        full_route = route["real_route"] + route["static_route"][1:]
        sampled_route = sample_route(full_route, 250)
        print(len(sampled_route))
        key = "FN7YD9KU9YMZ9GWQ27ECK7C2C"
        tomtomKey = "pz0l27KTUL4Vsu5jSlZ91Wt9yzcYqIRf"
        results = []

        for i, (lat, lng) in enumerate(sampled_route):
            print(f"🔁 Sampling point {i}: ({lat}, {lng})")
            traffic_data = get_traffic_data_point(lat, lng, tomtomKey)
            congestion = traffic_data["congestion"] if traffic_data else None
            elevation = get_elevation_point(lat, lng)
            road_score = compute_road_complexity_point(lat, lng)
            weather_data = get_weather_data_point(lat, lng, key)
            weather_score = compute_weather_score_point(weather_data) if weather_data else None
            building_score = compute_building_complexity_point(lat, lng)
            if(road_score):
                results.append({
                    "lat": lat,
                    "lng": lng,
                    "congestion": congestion,
                    "elevation": elevation,
                    "road_complexity": road_score,
                    "weather_score": weather_score,
                    "building_score": building_score,
                })

        heatmap = []
        feature_vectors = []
        valid_results = []
        for r in results:
            if None not in [r["congestion"], r["elevation"], r["road_complexity"], r["weather_score"], r["building_score"]]:
                feature_vectors.append([
                    r["congestion"],
                    r["elevation"],
                    r["road_complexity"],
                    r["weather_score"],
                    r["building_score"],
                ])
                valid_results.append(r)
        for i, r in enumerate(results):
         

            intensity = np.mean([
                normalize(r["congestion"]),
                normalize(r["elevation"]),
                normalize(r["road_complexity"]),
                normalize(r["weather_score"]),
                normalize(r["building_score"]),
            ])
            print(f"{i}: ({lat}, {lng}:{r['congestion']}, {r['elevation']}, {r['road_complexity']}, {r['weather_score']}, {r['building_score']}, {intensity}")
            heatmap.append({
                "lat": r["lat"],
                "lng": r["lng"],
                "score": intensity,
            })

        return heatmap

    @database_sync_to_async
    def get_route(self, order_id, lat, lng):
        try:
            
            G = load_graph_once()
            print(type(G))
            New_G = nx.subgraph(G, max(nx.strongly_connected_components(G), key=len)).copy()
            print(type(New_G))
            order = Order.objects.get(id=order_id)
            restaurant = Restaurant.objects.get(Rid=order.restaurant_id)
            rest_coords = (restaurant.latitude, restaurant.longitude)
            Dest_cords = (order.destination_lat, order.destination_lng)
            delivery_coords = (lat, lng)

            #G = get_graph_near_delivery(delivery_coords, rest_coords, buffer_km=15)
            #graph_path = os.path.join(settings.BASE_DIR, 'osm', 'taiwan_drive.graphml')
            #G = ox.load_graphml(graph_path)
            #print("finished loading path map")
            orig_node = ox.distance.nearest_nodes(New_G, delivery_coords[1], delivery_coords[0])
            dest_node = ox.distance.nearest_nodes(New_G, rest_coords[1], rest_coords[0])
            user_node = ox.distance.nearest_nodes(New_G, Dest_cords[1], Dest_cords[0])
            order_status = order.status
            print(order_status)
            if not nx.has_path(New_G, orig_node, dest_node):
                print("No path exists between origin and destination")
                return None
            if not nx.has_path(New_G, dest_node, user_node):
                print("No path exists between Restaurant and User")
                return None
            if(order_status != 'Food Done' or order_status != 'Completed'):

                # path = Short_path_Astar(New_G, orig_node, dest_node)
                
                # route_coords = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path]
                # dangerous_nodes = []
                # with ThreadPoolExecutor() as executor:
                #     futures = {executor.submit(score_node, node, G): node for node in path[1:3]}
                #     for future in as_completed(futures):
                #         result = future.result()
                #         if result:
                #             dangerous_nodes.append(result)
                # for node in path[1:3]:
                #     lat, lng = G.nodes[node]['y'], G.nodes[node]['x']
                #     diff = calcu_next_node(lat, lng)
                #     score = (
                #         normalize(diff["congestion"]) +
                #         normalize(diff["elevation"]) +
                #         normalize(diff["road_complexity"]) +
                #         normalize(diff["weather_score"]) +
                #         normalize(diff["building_score"])
                #     )
                #     if score > 0.7:
                #         dangerous_nodes.append(node)
                #     if dangerous_nodes:
                #         print(f"[get_route] Attempting to reroute around nodes: {dangerous_nodes}")
                #         new_path = Short_path_Astar(G, orig_node, dest_node, avoid_nodes=set(dangerous_nodes))
                #         if new_path:
                #             route_coords = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in new_path]
                #         dangerous_nodes = []
                # path_static = Short_path_Astar(New_G, dest_node, user_node)
                # route_coords_static = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path_static]
                # with ThreadPoolExecutor() as executor:
                #     futures = {executor.submit(score_node, node, G): node for node in path_static[1:3]}
                #     for future in as_completed(futures):
                #         result = future.result()
                #         if result:
                #             dangerous_nodes.append(result)
                # for node in path_static[1:3]:
                #     lat, lng = G.nodes[node]['y'], G.nodes[node]['x']
                #     diff = calcu_next_node(lat, lng)
                #     score = (
                #         normalize(diff["congestion"]) +
                #         normalize(diff["elevation"]) +
                #         normalize(diff["road_complexity"]) +
                #         normalize(diff["weather_score"]) +
                #         normalize(diff["building_score"])
                #     )
                #     if score > 0.7:
                #         dangerous_nodes.append(node)
                #     if dangerous_nodes:
                #         print(f"[get_route] Attempting to reroute around nodes: {dangerous_nodes}")
                #         new_path_static = Short_path_Astar(New_G, dest_node, user_node, avoid_nodes=set(dangerous_nodes))
                #         if new_path_static:
                #             route_coords_static = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in new_path_static]
                #         dangerous_nodes = []
                with ThreadPoolExecutor() as executor:
                # Step 1: Concurrent pathfinding
                    future_path_real = executor.submit(Short_path_Astar, New_G, orig_node, dest_node)
                    future_path_static = executor.submit(Short_path_Astar, New_G, dest_node, user_node)

                    path_real = future_path_real.result()
                    path_static = future_path_static.result()

                    if not path_real or not path_static:
                        print("[get_route] One or both paths could not be found.")
                        return None

                    # Step 2: Concurrent scoring and rerouting
                    future_real = executor.submit(compute_route_segment, G, New_G, path_real, orig_node, dest_node)
                    future_static = executor.submit(compute_route_segment, G, New_G, path_static, dest_node, user_node)

                    route_coords = future_real.result()
                    route_coords_static = future_static.result()

                fallback_line = interpolate_line(delivery_coords, rest_coords)
                dist_km = geodesic(delivery_coords, rest_coords).km
                return {
                        "real_route": route_coords,
                        "static_route": route_coords_static,
                        "fallback_line": fallback_line,
                        "distance": dist_km,
                        }
            elif order_status == 'Food Done':
                path = Short_path_Astar(New_G, orig_node, user_node)
                route_coords = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path]
                dangerous_nodes = []
                for node in path[1:4]:
                    lat, lng = G.nodes[node]['y'], G.nodes[node]['x']
                    diff = calcu_next_node(lat, lng)
                    score = (
                        normalize(diff["congestion"]) +
                        normalize(diff["elevation"]) +
                        normalize(diff["road_complexity"]) +
                        normalize(diff["weather_score"]) +
                        normalize(diff["building_score"])
                    )
                    if score > 3.5:
                        dangerous_nodes.append(node)
                    if dangerous_nodes:
                        print(f"[get_route] Attempting to reroute around nodes: {dangerous_nodes}")
                        new_path = Short_path_Astar(G, orig_node, dest_node, avoid_nodes=set(dangerous_nodes))
                        if new_path:
                            route_coords = [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in new_path]
                        dangerous_nodes = []
                fallback_line = interpolate_line(delivery_coords, Dest_cords)
                dist_km = geodesic(delivery_coords, Dest_cords).km
                return {
                        "real_route": route_coords,
                        
                        "fallback_line": fallback_line,
                        "distance": dist_km,
                        }
        except Exception as e:
            print(f"[Route Error] {str(e)}")
            return None
        
    # @database_sync_to_async
    # def save_frame(self, order_id,lat,lng, TimeNum):
    #     key = "AIzaSyDRPaAyw-McbHYiboHfXCEExlK7zGXrPOg"
    #     actual_lat, actual_lng = find_nearby_streetview(lat, lng, key)

    #     if actual_lat is None:
    #         print(f"No nearby Street View found for {lat}, {lng}")
    #         return

    #     location = f"{actual_lat},{actual_lng}"
    #     heading = 90
    #     pitch = 0
    #     fov = 90

    #     url = f'https://maps.googleapis.com/maps/api/streetview?size=640x640&location={location}&heading={heading}&pitch={pitch}&fov={fov}&key={key}'
    #     r = requests.get(url)

    #     if r.status_code == 200:
    #         file_name = f"{order_id}_streetview_{TimeNum}.jpg"
    #         image_file = ContentFile(r.content, name=file_name)
    #         try:
    #             the_order = Order.objects.get(id=order_id)
    #             VideoFrame.objects.create(order=the_order, latitude=actual_lat, longitude=actual_lng, frame=image_file)
    #         except Order.DoesNotExist:
    #             print(f"Order {order_id} not found.")
    #     else:
    #         print(f"Image request failed with status: {r.status_code}")

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
            #dest = order.destination
            #city = extract_city(dest)
            #print(city)  
            #city_bounds = {
             #   "高雄市": {
              #      "min_lat": 22.5,
               #     "max_lat": 22.8,
                #    "min_lng": 120.2,
                 #   "max_lng": 120.4
                #}
            #}
            #grid = generate_grid(city, city_bounds)
            #grid = add_default_features(grid)
            #grid = predict_grid_delivery_times(grid)
            
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
                return trial_lat, trial_lng 
    return None, None 


def Short_path_Astar(G, start, goal, avoid_nodes=None):
   
    counter = count() #avoids uneccesary comparisons between points wit hsame priority
    frontier = [(0, next(counter), start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    avoid_nodes = avoid_nodes or set()
    goal_y, goal_x = G.nodes[goal]['y'], G.nodes[goal]['x']
    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for neighbor in G.neighbors(current):
            if neighbor in avoid_nodes:
                continue

            # Handle both MultiDiGraph and DiGraph edge access
            
            data = G.get_edge_data(current, neighbor)
            if data is None:
                continue

            # Choose the first edge if MultiDiGraph
            if isinstance(data, dict) and 0 in data:
                weight = data[0].get('length', float('inf'))
            else:
                weight = data.get('length', float('inf'))

            if weight == float('inf'):
                continue
         

            new_cost = cost_so_far[current] + weight

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + euclidean_coords(goal_y, goal_x, G.nodes[neighbor]['y'], G.nodes[neighbor]['x']) #euclidean_heuristic(G.nodes[goal], G.nodes[neighbor])
                heapq.heappush(frontier, (priority, next(counter), neighbor))
                came_from[neighbor] = current

    # Reconstruct path
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from.get(current)
        if current is None:
            print("[Short_path_Astar] Path reconstruction failed — no route back to start")
            return None
    path.append(start)
    path.reverse()
    return path



# def euclidean_heuristic(a, b):
#     """
#     Calculates straight-line distance.
#     Supports:
#     - a, b as (y, x) tuples (i.e., (lat, lng))
#     - a, b as node dictionaries with 'x' and 'y'
#     """
#     try:
#         if isinstance(a, dict):
#             y1, x1 = a['y'], a['x']
#         else:
#             y1, x1 = a

#         if isinstance(b, dict):
#             y2, x2 = b['y'], b['x']
#         else:
#             y2, x2 = b

#         return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
#     except Exception as e:
#         print(f"[Heuristic Error] {e} for a={a}, b={b}")
#         return float('inf')

def euclidean_heuristic(a, b): #get distance between nodes
    return sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2) 

def euclidean_coords(y1, x1, y2, x2):
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def sample_route(route, min_distance_m=500):
    if not route:
        return []

    sampled = [route[0]]
    last_point = route[0]

    for point in route[1:]:
        dist = geodesic((last_point[0], last_point[1]), (point[0], point[1])).meters
        if dist >= min_distance_m:
            sampled.append(point)
            last_point = point

    # Ensure the last point is included
    if sampled[-1] != route[-1]:
        sampled.append(route[-1])

    return sampled

'''
def sample_route(route, step=10):
    return route[::step] + [route[-1]]

def get_traffic_data(sampled_coords, tomtom_key):
    results = []
    for lat, lng in sampled_coords:
        url = (
            "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            f"?point={lat},{lng}&key={tomtom_key}"
        )
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            results.append({
                "point": (lat, lng),
                "traffic": data.get("flowSegmentData", {}).get("currentSpeed", None),
                "congestion": ( 1 - data["flowSegmentData"]["currentSpeed"] / data["flowSegmentData"]["freeFlowSpeed"])
            })
    return results


def get_elevation(coords):
    location_str = "|".join([f"{lat},{lng}" for lat, lng in coords])
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={location_str}"
    res = requests.get(url)
    if res.status_code == 200:
        return [point["elevation"] for point in res.json()["results"]]
    return []

def elevation_gain(elevations):
    gain = 0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i-1]
        if diff > 0:
            gain += diff
    return gain



def compute_road_complexity_score(route_coords, buffer_m=500):
    # 1. Create bounding box around route
    line = LineString([(lng, lat) for lat, lng in route_coords])  # (x, y)
    buffered_area = line.buffer(buffer_m / 111320)  # rough meters to degrees
    G_full = load_graph_once()  
    nodes_in_area = [
        node for node, data in G_full.nodes(data=True)
        if buffered_area.contains(Point(data['x'], data['y']))
    ]
    G = G_full.subgraph(nodes_in_area).copy()

    if len(G.nodes) == 0:
        return 0  # No data, fallback to zero complexity

    # --- Intersection Density ---
    area_km2 = ox.project_gdf(ox.graph_to_gdfs(G, nodes=False)).unary_union.area / 1e6
    intersections = [node for node, degree in dict(G.degree()).items() if degree > 2]
    intersection_density = len(intersections) / area_km2 if area_km2 > 0 else 0

    # --- Edge Length Variability ---
    lengths = [d["length"] for u, v, d in G.edges(data=True) if "length" in d]
    edge_variability = np.std(lengths) / np.mean(lengths) if lengths else 0

    # --- Clustering Coefficient ---
    clustering = nx.average_clustering(G.to_undirected())

    # --- Dead Ends ---
    dead_ends = sum(1 for _, d in G.degree() if d == 1)
    dead_end_ratio = dead_ends / len(G.nodes) if G.number_of_nodes() > 0 else 0

    # --- Normalize & Combine (tune weights as needed) ---
    norm = lambda x: x / (x + 1)  # sigmoid-like, simple normalization
    score = (
        0.4 * norm(intersection_density) +
        0.2 * norm(edge_variability) +
        0.2 * norm(clustering) +
        0.2 * norm(dead_end_ratio)
    )
    return round(score, 3)


def get_weather_data(sampled_coords, key):
    results = []
    for lat, lng in sampled_coords:
        url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lng}&appid={key}&units=metric"
        )
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            results.append({
                "temp": data["main"]["temp"],
                "rain": data.get("rain", {}).get("1h", 0),
                "wind_speed": data["wind"]["speed"],
                "visibility": data.get("visibility", 10000),
                "thunder": any("thunderstorm" in w["main"].lower() for w in data["weather"]),
            })
        else:
            print("Weather API error:", res.status_code, res.text)
            return None
    return results


def compute_weather_score(weather):
    score = 0
    for i in weather:
        # weather is a dict with keys: temp, rain, wind_speed, visibility, thunder
        # Temperature extremes
        if i["temp"] < 5 or i["temp"] > 35:
            score += 0.2

        # Rainfall intensity
        if i["rain"] > 0:
            score += min(i["rain"] / 20, 0.3)  # cap at 0.3

        # Wind speed
        if i["wind_speed"] > 5:
            score += min(i["wind_speed"] / 20, 0.2)  # cap at 0.2

        # Poor visibility
        if i["visibility"] < 2000:
            score += 0.1

        # Storms/thunder present
        if i.get("thunder", False):
            score += 0.2

    return round(min(score, 1.0), 3)



def compute_building_complexity_score(route_coords, buffer_m=300):
    # Convert to LineString and buffer the route area
    line = LineString([(lng, lat) for lat, lng in route_coords])
    buffered_area = line.buffer(buffer_m / 111320)  # meters to degrees approx

    # Download building footprints in the area
    tags = {'building': True}
    try:
        buildings = ox.geometries_from_polygon(buffered_area, tags)
    except Exception as e:
        print("OSM building query error:", e)
        return 0

    if buildings.empty:
        return 0

    # Filter polygons only
    buildings = buildings[buildings.geom_type == "Polygon"]

    # --- Metrics ---
    num_buildings = len(buildings)
    area_km2 = buffered_area.area * (111.32 ** 2)  # degrees² to km² rough conversion
    building_density = num_buildings / area_km2 if area_km2 > 0 else 0

    # Area variance (proxy for layout complexity)
    building_areas = [poly.area for poly in buildings.geometry]
    area_variance = np.std(building_areas) / np.mean(building_areas) if building_areas else 0

    # --- Normalize & Combine ---
    norm = lambda x: x / (x + 1)  # same as before
    score = (
        0.6 * norm(building_density) +
        0.4 * norm(area_variance)
    )
    return round(score, 3)
    '''

def get_traffic_data_point(lat, lng, tomtom_key):
    url = (
        "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        f"?point={lat},{lng}&key={tomtom_key}"
    )
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json().get("flowSegmentData", {})
        current = data.get("currentSpeed")
        free = data.get("freeFlowSpeed", 1)
        congestion = 1 - (current / free) if current is not None else None
        print(f"Success for traffic data: {current}, {free}, {congestion}")
        return {"traffic": current, "congestion": congestion}
    return None


def get_elevation_point(lat, lng):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lng}"
    res = requests.get(url)
    if res.status_code == 200:
        
        ele = res.json()["results"][0]["elevation"]
        print(f"success for elevation: {ele}")
        return res.json()["results"][0]["elevation"]
    return None


def compute_elevation_gain_point(prev_elev, current_elev):
    return max(0, current_elev - prev_elev)


def compute_road_complexity_point(lat, lng, buffer_m=500):
    point = Point(lng, lat)
    buffer_deg = buffer_m / 111320
    buffered_area = point.buffer(buffer_deg)
    G_full = load_graph_once()

    nodes_in_area = [
        node for node, data in G_full.nodes(data=True)
        if buffered_area.contains(Point(data['x'], data['y']))
    ]
    G = G_full.subgraph(nodes_in_area).copy()

    if len(G.nodes) == 0:
        return 0
    if len(G.edges) == 0:
        print("No edges found in subgraph.")
        return 0

    try:
        G_proj = ox.project_graph(G)
        gdf_edges = ox.graph_to_gdfs(G_proj, nodes=False)
    except Exception as e:
        print(f"Graph projection or conversion failed: {e}")
        return None
    
    area_km2 = gdf_edges.unary_union.convex_hull.area / 1e6
    intersections = [node for node, deg in G.degree() if deg > 2]
    intersection_density = len(intersections) / area_km2 if area_km2 > 0 else 0

    lengths = [d["length"] for _, _, d in G.edges(data=True) if "length" in d]
    edge_variability = np.std(lengths) / np.mean(lengths) if lengths else 0

    simple_graph = nx.Graph(G.to_undirected())  
    clustering = nx.average_clustering(simple_graph)

    dead_ends = sum(1 for _, deg in G.degree() if deg == 1)
    dead_end_ratio = dead_ends / len(G.nodes)

    norm = lambda x: x / (x + 1)
    score = (
        0.4 * norm(intersection_density) +
        0.2 * norm(edge_variability) +
        0.2 * norm(clustering) +
        0.2 * norm(dead_end_ratio)
    )
    print(f"complete road complexity: {score}")
    return round(score, 3)


def get_weather_data_point(lat, lng, key):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lng}/today?unitGroup=metric&include=current&key={key}&contentType=json"
    res = requests.get(url)
    if res.status_code == 200:
        print("success for weather")
        data = res.json()
        current = data.get("currentConditions", {})
        return {
            "temp": current.get("temp"),
            "rain": current.get("precip") or 0,
            "wind_speed": current.get("windspeed"),
            "visibility": current.get("visibility"),
            "thunder": "thunder" in current.get("conditions", "").lower(),
        }
    return None


def compute_weather_score_point(weather):
    score = 0
    if weather["temp"] < 5 or weather["temp"] > 35:
        score += 0.2
    if weather["rain"] > 0:
        score += min(weather["rain"] / 20, 0.3)
    if weather["wind_speed"] > 5:
        score += min(weather["wind_speed"] / 20, 0.2)
    if weather["visibility"] < 2000:
        score += 0.1
    if weather.get("thunder", False):
        score += 0.2
    print(f"weather score: {score}")
    return round(min(score, 1.0), 3)


def compute_building_complexity_point(lat, lng, buffer_m=500):
    point = Point(lng, lat)
    buffer_deg = buffer_m / 111320
    buffered_area = point.buffer(buffer_deg)
    tags = {'building': True}
    try:
        buildings = features.features_from_polygon(buffered_area, tags)
    except Exception as e:
        print("Building query error:", e)
        return 0

    buildings = buildings[buildings.geom_type == "Polygon"]
    if buildings.empty:
        return 0

    num_buildings = len(buildings)
    area_km2 = buffered_area.area * (111.32 ** 2)
    density = num_buildings / area_km2

    building_areas = [poly.area for poly in buildings.geometry]
    area_variance = np.std(building_areas) / np.mean(building_areas) if building_areas else 0

    norm = lambda x: x / (x + 1)
    score = 0.6 * norm(density) + 0.4 * norm(area_variance)
    print(f"success for building complexity: {score}")
    return round(score, 3)


def normalize(x):
    return x / (x + 1) if x is not None else 0


# def extract_city(address):
#     match = re.search(r'(\d+)?([^\d市]+市)', address)
#     if match:
#         return match.group(2)  # '高雄市'
#     return None


# def generate_grid(city_name, city_bounds,step=0.01):
#     bounds = city_bounds.get(city_name)
#     if not bounds:
#         return []

#     lat_range = np.arange(bounds["min_lat"], bounds["max_lat"], step)
#     lng_range = np.arange(bounds["min_lng"], bounds["max_lng"], step)

#     grid_points = [
#         {"lat": lat, "lng": lng}
#         for lat in lat_range
#         for lng in lng_range
#     ]
#     return pd.DataFrame(grid_points)


# def add_default_features(grid_df):
#     grid_df['congestion'] = 0.5
#     grid_df['elevation_gain'] = 10
#     grid_df['road_complexity'] = 0.5
#     grid_df['building_complexity'] = 0.5
#     grid_df['weather_score'] = 0.5
#     grid_df['hour_sin'] = 0  # noon
#     grid_df['hour_cos'] = 1
#     grid_df['day_sin'] = 0
#     grid_df['day_cos'] = 1
#     grid_df['is_rush_hour'] = 0
#     grid_df['is_weekend'] = 0
#     return grid_df


# def predict_grid_delivery_times(grid_df):
#     model = joblib.load("model/delivery_model.pkl")
#     features = [
#         'congestion', 'elevation_gain', 'road_complexity',
#         'building_complexity', 'weather_score',
#         'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
#         'is_rush_hour', 'is_weekend'
#     ]
#     grid_df['predicted_time'] = model.predict(grid_df[features])
#     return grid_df



def calcu_next_node(lat,lng):
    print(f"🔁 Sampling point: ({lat}, {lng})")
    key = "FN7YD9KU9YMZ9GWQ27ECK7C2C"
    tomtomKey = "pz0l27KTUL4Vsu5jSlZ91Wt9yzcYqIRf"
    traffic_data = get_traffic_data_point(lat, lng, tomtomKey)
    congestion = traffic_data["congestion"] if traffic_data else None
    elevation = get_elevation_point(lat, lng)
    #road_score = compute_road_complexity_point(lat, lng)
    road_score = get_cached_road_complexity_by_location(lat,lng)
    weather_data = get_weather_data_point(lat, lng, key)
    print(weather_data)
    weather_score = compute_weather_score_point(weather_data) if weather_data else 0
    building_score = compute_building_complexity_point(lat, lng)

    return {
                "lat": lat,
                "lng": lng,
                "congestion": congestion,
                "elevation": elevation,
                "road_complexity": road_score,
                "weather_score": weather_score,
                "building_score": building_score,
    }


def get_bounds(city_name):
    try:
        KNOWN_BOUNDS = {
            "Taipei": {
                "min_lat": 25.01, "max_lat": 25.13,
                "min_lng": 121.45, "max_lng": 121.60
            },
            "New Taipei": {
                "min_lat": 24.90, "max_lat": 25.30,
                "min_lng": 121.25, "max_lng": 121.65
            },
            "Taoyuan": {
                "min_lat": 24.75, "max_lat": 25.10,
                "min_lng": 121.05, "max_lng": 121.35
            },
            "Hsinchu": {
                "min_lat": 24.75, "max_lat": 24.90,
                "min_lng": 120.85, "max_lng": 121.00
            },
            "Taichung": {
                "min_lat": 24.00, "max_lat": 24.40,
                "min_lng": 120.50, "max_lng": 120.80
            },
            "Changhua": {
                "min_lat": 23.85, "max_lat": 24.10,
                "min_lng": 120.35, "max_lng": 120.65
            },
            "Tainan": {
                "min_lat": 22.85, "max_lat": 23.15,
                "min_lng": 120.10, "max_lng": 120.35
            },
            "Kaohsiung": {
                "min_lat": 22.28, "max_lat": 23.28,
                "min_lng": 120.10, "max_lng": 121.01
            },
            "Keelung": {
                "min_lat": 25.08, "max_lat": 25.17,
                "min_lng": 121.70, "max_lng": 121.80
            },
            "Yilan": {
                "min_lat": 24.60, "max_lat": 24.80,
                "min_lng": 121, "max_lng": 121.85
            },
            "Hualien": {
                "min_lat": 23.80, "max_lat": 24.10,
                "min_lng": 121.45, "max_lng": 121.65
            },
            "Taitung": {
                "min_lat": 22.70, "max_lat": 23.30,
                "min_lng": 120.95, "max_lng": 121.25
            },
            "Penghu": {
                "min_lat": 23.17, "max_lat": 23.73,
                "min_lng": 119.30, "max_lng": 119.70
            },
            "Chiayi": {
                "min_lat": 23.40, "max_lat": 23.55,
                "min_lng": 120.40, "max_lng": 120.55
            },
            "Miaoli": {
                "min_lat": 24.30, "max_lat": 24.65,
                "min_lng": 120.70, "max_lng": 121.10
            },
            "Nantou": {
                "min_lat": 23.50, "max_lat": 24.10,
                "min_lng": 120.70, "max_lng": 121.10
            },
            "Yunlin": {
                "min_lat": 23.50, "max_lat": 23.90,
                "min_lng": 120.15, "max_lng": 120.55
            },
            "Pingtung": {
                "min_lat": 21.90, "max_lat": 22.70,
                "min_lng": 120.40, "max_lng": 120.80
            }
        }

        return {
            "min_lat": KNOWN_BOUNDS[city_name]["min_lat"],
            "max_lat": KNOWN_BOUNDS[city_name]["max_lat"],
            "min_lng": KNOWN_BOUNDS[city_name]["min_lng"],
            "max_lng": KNOWN_BOUNDS[city_name]["max_lng"]
        }
    except Exception as e:
        print(f"[City Bounds Error] {str(e)}")
        return None
    

def generate_grid(city_name, step=0.01, jitter=0):
    city_bounds = get_bounds(city_name)
    if not city_bounds:
        return pd.DataFrame()

    lat_range = np.arange(city_bounds["min_lat"], city_bounds["max_lat"], step)
    lng_range = np.arange(city_bounds["min_lng"], city_bounds["max_lng"], step)

    grid_points = [
        {
            "lat": lat + np.random.uniform(-jitter, jitter),
            "lng": lng + np.random.uniform(-jitter, jitter)
        }
        for lat in lat_range
        for lng in lng_range
    ]
    return pd.DataFrame(grid_points)


def generate_random_points(city_name, num_points=200):
    city_bounds = get_bounds(city_name)
 
    print(f"[DEBUG] Bounds for {city_name}: {city_bounds}")
    if not city_bounds:
        return pd.DataFrame()

    points = []
    attempts = 0
    max_attempts = 5000  # fail-safe

    while len(points) < num_points and attempts < max_attempts:
        lat = np.random.uniform(city_bounds["min_lat"], city_bounds["max_lat"])
        lng = np.random.uniform(city_bounds["min_lng"], city_bounds["max_lng"])

      

        if is_land(lat, lng):
            points.append({"lat": lat, "lng": lng})
        attempts += 1

    print(f"[POINT GEN] Successfully generated {len(points)} valid points out of {attempts} attempts")
    return pd.DataFrame(points)

# def generate_random_points(city_name, min_rings=2, points_per_ring=7,ring_density_factor=1.5, max_rings = 8):
#     center_df["City"] = center_df["district_name"].str[:3].apply(translate_city_name)
#     center_df["District"] = center_df["district_name"].str[3:]
    
#     # Prepare area_df for merge (ensure clean strings)
#     area_df["area"] = area_df["area"].str.strip()
#     area_df["City"] = area_df["City"].str.strip()

#     # Merge on city + district
#     merged_df = center_df.merge(
#     area_df,
#     left_on=["City", "District"],
#     right_on=["City", "area"],
#     how="left"
#     )
#     filtered = merged_df[merged_df["City"] == city_name]
#     if filtered.empty:
#         print(f"[ERROR] No districts found for city: {city_name}")
#         return pd.DataFrame()

#     all_points = []
#     for _, row in filtered.iterrows():
#         center_lat = float(row["center_lat"])
#         center_lng = float(row["center_lng"])
#         area_km2 = float(row["size"]) if not pd.isna(row["size"]) else 1  # fallback

#         # Adaptive rings
#         estimated_rings = int(math.sqrt(area_km2) / ring_density_factor)
#         num_rings = max(min_rings, min(max_rings, estimated_rings))

#         fan_points = generate_fan_out_points(center_lat, center_lng, num_rings=num_rings, points_per_ring=points_per_ring)
#         all_points.extend(fan_points)

#     print(f"[POINT GEN] Generated {len(all_points)} points for city: {city_name}")
#     return pd.DataFrame(all_points)
    # filtered_centers = center_df[center_df["City"] == city_name]
    # if filtered_centers.empty:
    #     print(f"[ERROR] No districts found for city: {city_name}")
    #     return pd.DataFrame()

    # all_points = []
    # for _, row in filtered_centers.iterrows():
    #     center_lat = float(row["center_lat"])
    #     center_lng = float(row["center_lng"])
    #     fan_points = generate_fan_out_points(center_lat, center_lng, num_rings=num_rings, points_per_ring=points_per_ring)
    #     all_points.extend(fan_points)

    # print(f"[POINT GEN] Generated {len(all_points)} points for city: {city_name}")
    # return pd.DataFrame(all_points)

road_complexity_df = pd.read_csv("data/taiwan_city_road_complexity_300.csv")
class HeatMapConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"[RECEIVE] WebSocket data: {data}")
        if data['type'] == 'UpdateDiff':
            Dest_addr = data['Dest_address']
            Rest_addr = data['Rest_address']
            Updateoid = data["Oid"]
            order = await sync_to_async(Order.objects.get)(id=Updateoid)
            if order.points == 0:
                dest_lat, dest_lng = get_coordinates(Dest_addr)
                Rest_lat, Rest_lng = get_coordinates(Rest_addr)
                dest_diff = calcu_next_node(dest_lat, dest_lng)
                dest_score = (
                        normalize(dest_diff["congestion"]) +
                        normalize(dest_diff["elevation"]) +
                        normalize(dest_diff["road_complexity"]) +
                        normalize(dest_diff["weather_score"]) +
                        normalize(dest_diff["building_score"])
                    )
                Rest_diff = calcu_next_node(Rest_lat, Rest_lng)
                Rest_score = (
                        normalize(Rest_diff["congestion"]) +
                        normalize(Rest_diff["elevation"]) +
                        normalize(Rest_diff["road_complexity"]) +
                        normalize(Rest_diff["weather_score"]) +
                        normalize(Rest_diff["building_score"])
                    )
                avg = (dest_score + Rest_score) / 2
                print(Rest_score)
                print(dest_score) 
                point = 0
                print(avg)
                if avg <= 2:
                    point = 1
                elif avg > 2 and avg <= 3:
                    point = 2
                elif avg >3 and avg <= 4:
                    point = 3
                else:
                    point = 4
            
               
                order.points = point
                await sync_to_async(order.save)()

                await self.send(text_data=json.dumps({
                "type": "UpdatePoints",
                "stat": "success",
                }))

        if data['type'] == 'Prediction_info':
            
            print("[INFO] Loading ML model...")
            model = joblib.load('model/delivery_model.pkl')

            city = data["city"]
            grid = generate_random_points(city)
            print(f"[INFO] Generated {len(grid)} grid points for {city}")
            if data['dest_node']:
                dest_lat = data['dest_node'].split(":")[0]
                dest_lng = data['dest_node'].split(":")[1]
                key = "FN7YD9KU9YMZ9GWQ27ECK7C2C"
                weather = get_weather_data_point(dest_lat, dest_lng, key)
            else:
                weather = {
                    "temp": data.get("temp", 25), 
                    "rain": data.get("rain", 0),
                    "wind_speed": data.get("wind_speed", 2),
                    "visibility": data.get("visibility", 10),
                    "thunder": data.get("thunder", 0)
                }

            weather_score = compute_weather_score_point(weather)
            print(f"[INFO] Weather score: {weather_score}")

            weekday = data['weekday']
            time = data['time']
            print(weekday)
            print(time)
            congestion_Record = pd.read_csv("data/taiwan_simulated_congestion_by_time.csv")
            avg_elevation = pd.read_csv("data/taiwan_city_average_elevations.csv")
            
            filtered = congestion_Record[
                (congestion_Record["city"] == city) &
                (congestion_Record["hour"] == time) &
                (congestion_Record["day_of_week"] == weekday)
            ]

            congestion_score = filtered["congestion_level"].mean() if not filtered.empty else 0
            print(f"[INFO] Congestion score: {congestion_score}")
            preload_graph()
            print("[INFO] Starting asynchronous feature computation for all points...")
            results = await process_in_batches(
                grid,                
                batch_size=30,      
                city=city,
                avg_elevation=avg_elevation,
                weather_score=weather_score,
                congestion_score=congestion_score,
                time=time,
                weekday=weekday,
                model=model
            )
            heatmap_data = [r for r in results if r is not None]
            print(f"[INFO] Finished computing. {len(heatmap_data)} valid predictions.")

            bounds = get_bounds(city)
            print(f"[INFO] Bounds: {bounds}")
            print(f"[WS SEND] Sending heatmap with {len(heatmap_data)} points")
            if data['dest_node'] is not None and data['rest_node'] is not None:
                dest_lat = data['dest_node'].split(":")[0]
                dest_lng = data['dest_node'].split(":")[1]
                dest_diff = calcu_next_node(dest_lat, dest_lng)
                dest_score = (
                        normalize(dest_diff["congestion"]) +
                        normalize(dest_diff["elevation"]) +
                        normalize(dest_diff["road_complexity"]) +
                        normalize(dest_diff["weather_score"]) +
                        normalize(dest_diff["building_score"])
                    )
                Rest_lat = data['rest_node'].split(":")[0]
                Rest_lng = data['rest_node'].split(":")[1]
                Rest_diff = calcu_next_node(Rest_lat, Rest_lng)
                Rest_score = (
                        normalize(Rest_diff["congestion"]) +
                        normalize(Rest_diff["elevation"]) +
                        normalize(Rest_diff["road_complexity"]) +
                        normalize(Rest_diff["weather_score"]) +
                        normalize(Rest_diff["building_score"])
                    )
                print(dest_score)
                print(Rest_score)
                avg = (dest_score + Rest_score) / 2
                point = 0
                if avg <= 2:
                    point = 1
                elif avg > 2 and avg <= 3:
                    point = 2
                elif avg >3 and avg <= 4:
                    point = 3
                else:
                    point = 4
                oid = data['oid']
                order = await sync_to_async(Order.objects.get)(id=oid)
                if order.points == 0:
                    order.points = point
                    await sync_to_async(order.save)()

                await self.send(text_data=json.dumps({
                "type": "HeatMap",
                "heatmap": heatmap_data,
                "bounds": {
                    "sw": {"lat": bounds["min_lat"], "lng": bounds["min_lng"]},
                    "ne": {"lat": bounds["max_lat"], "lng": bounds["max_lng"]},
                },
                "Dest_score": dest_score,
                "Rest_score": Rest_score,
                }))

            await self.send(text_data=json.dumps({
                "type": "HeatMap",
                "heatmap": heatmap_data,
                "bounds": {
                    "sw": {"lat": bounds["min_lat"], "lng": bounds["min_lng"]},
                    "ne": {"lat": bounds["max_lat"], "lng": bounds["max_lng"]}
                }
            }))

                
                

                
                
async def compute_point_features(row, city, avg_elevation, weather_score, congestion_score, time, weekday, model):
    lat = row['lat']
    lng = row['lng']
    loop = asyncio.get_running_loop()

    print(f"[TASK START] ({lat}, {lng})")

    try:
        ele, building_complexity, road_complexity = await asyncio.gather(
            loop.run_in_executor(executor, get_elevation_point, lat, lng),
            loop.run_in_executor(executor, compute_building_complexity_point, lat, lng),
            loop.run_in_executor(executor, get_cached_road_complexity, lat,lng, city),
        )
        #road_complexity = 0.5
        if road_complexity is None:
            print(f"[SKIP] No road data at ({lat}, {lng})")
            return None

        if ele is None:
            print(f"[FALLBACK] Missing elevation at ({lat}, {lng}) -> using 0")
            ele = 0

        if building_complexity is None:
            print(f"[FALLBACK] Missing building complexity at ({lat}, {lng}) -> using 0")
            building_complexity = 0

        city_avg_ele = avg_elevation.loc[avg_elevation["city"] == city, "avg_elevation_m"].values[0]
        ele_score = ele - city_avg_ele

        num_day = int(weekday)
        num_time = int(time)
        hour_sin = math.sin(2 * math.pi * num_time / 24)
        hour_cos = math.cos(2 * math.pi * num_time / 24)
        day_sin = math.sin(2 * math.pi * num_day / 7)
        day_cos = math.cos(2 * math.pi * num_day / 7)

        is_rush_hour = 1 if num_time in [7, 8, 9, 16, 17, 18] else 0
        is_weekend = 1 if num_day in [5, 6] else 0
        
        features = [
            weather_score,
            congestion_score,
            ele_score,
            building_complexity,
            road_complexity,
            hour_sin,
            hour_cos,
            day_sin,
            day_cos,
            is_rush_hour,
            is_weekend
        ]

        prediction = model.predict([features])[0]
        print(f"[PREDICT] ({lat}, {lng}) -> {prediction:.2f}")

        return {
            "lat": lat,
            "lng": lng,
            "value": prediction
        }

    except Exception as e:
        print(f"[ERROR] ({lat}, {lng}) failed: {e}")
        return None



async def compute_point_features_throttled(row, city, avg_elevation, weather_score, congestion_score, time, weekday, model):
    print("[SEMAPHORE] Waiting for slot...")
    async with semaphore:
        print("[SEMAPHORE] Slot acquired")
        await asyncio.sleep(0.1)
        for attempt in range(2):  # try up to 2 times
            try:
                return await asyncio.wait_for(
                    compute_point_features(row, city, avg_elevation, weather_score, congestion_score, time, weekday, model),
                    timeout=30
                )
            except asyncio.TimeoutError:
                print(f"[TIMEOUT] ({row['lat']}, {row['lng']}) attempt {attempt+1} failed")
        print(f"[TIMEOUT] Skipped point ({row['lat']}, {row['lng']}) after retries")
        return None
    


async def process_in_batches(grid_df, batch_size, city, avg_elevation, weather_score, congestion_score, time, weekday, model):
    results = []
    total = len(grid_df)
    for i in range(0, total, batch_size):
        print(f"[BATCH] Processing rows {i} to {min(i + batch_size, total)}...")
        batch = grid_df.iloc[i:i+batch_size]
        tasks = [
            compute_point_features_throttled(row, city, avg_elevation, weather_score, congestion_score, time, weekday, model)
            for _, row in batch.iterrows()
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    return results



def preload_graph():
    
    print("[PRELOAD] Ensuring road graph is loaded...")
    _ = load_graph_once()
    print("[PRELOAD] Road graph loaded.")



async def compute_road_complexity_async(lat, lng):
    loop = asyncio.get_running_loop()
    async with road_semaphore:
        return await loop.run_in_executor(executor, compute_road_complexity_point, lat, lng)
    



async def compute_road_complexity_async(lat, lng):
    loop = asyncio.get_running_loop()
    async with road_semaphore:
        print(f"[ROAD START] ({lat}, {lng})")
        result = await loop.run_in_executor(executor, compute_road_complexity_point, lat, lng)
        print(f"[ROAD DONE] ({lat}, {lng}) = {result}")
        return result
    


# def get_cached_road_complexity(lat, lng, city):
#     print(city)
#     candidates = road_complexity_df[road_complexity_df["city"] == city]
#     if candidates.empty:
#         return 0.5
#     distances = (candidates["lat"] - lat)**2 + (candidates["lng"] - lng)**2
#     cand = candidates.iloc[distances.idxmin()]["road_complexity"]
#     print(f"success for road complexity: {cand}")
#     return candidates.iloc[distances.idxmin()]["road_complexity"]

def get_cached_road_complexity(lat, lng, city):
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        print(f"[RC][ERROR] Invalid lat/lng values: lat={lat}, lng={lng}")
        return 0.5

    # Check if the city is in the dataset at all
    available_cities = road_complexity_df["city"].unique()
    if city not in available_cities:
        print(f"[RC][WARNING] City '{city}' not found in road_complexity_df. Available cities: {list(available_cities)}")
        return 0.5
    # road_complexity_df["lat"] = pd.to_numeric(road_complexity_df["lat"], errors="coerce")
    # road_complexity_df["lng"] = pd.to_numeric(road_complexity_df["lng"], errors="coerce")
    # road_complexity_df.dropna(subset=["lat", "lng"], inplace=True)
    # Filter for matching city
    candidates = road_complexity_df[road_complexity_df["city"] == city]
 

    if candidates.empty:
        print(f"[RC][ERROR] No candidates found for city '{city}'")
        return 0.5

    # Compute closest point
    
    distances = (candidates["lat"] - lat)**2 + (candidates["lng"] - lng)**2
    idx_closest = distances.idxmin()

    if pd.isna(idx_closest):
        print(f"[RC][ERROR] idxmin() failed. No closest point found.")
        return 0.5

    cand_value = candidates.loc[idx_closest]["road_complexity"]
    print(f"[RC][SUCCESS] Closest road complexity for ({lat}, {lng}) in {city} is {cand_value}")
    return cand_value


def generate_fan_out_points(center_lat, center_lng, num_rings=2, points_per_ring=8, spacing_m=400):
    points = []
    radius_step_deg = spacing_m / 111320  # approx degrees per meter (lat)

    for ring in range(1, num_rings + 1):
        radius = ring * radius_step_deg
        offset_angle = (360 / points_per_ring) / 2 * (ring % 2)  # alternate offset every other ring
        for i in range(points_per_ring):
            angle_deg = i * (360 / points_per_ring) + offset_angle
            angle_rad = math.radians(angle_deg)
            dlat = radius * math.sin(angle_rad)
            dlng = radius * math.cos(angle_rad) / math.cos(math.radians(center_lat))
            points.append({
                "lat": center_lat + dlat,
                "lng": center_lng + dlng,
                "ring": ring,
                "angle": angle_deg
            })
    return points



def translate_city_name(ch_name):
    match ch_name:
        case "臺北市" | "台北市":
            return "Taipei"
        case "新北市":
            return "New Taipei"
        case "桃園市":
            return "Taoyuan"
        case "臺中市" | "台中市":
            return "Taichung"
        case "臺南市" | "台南市":
            return "Tainan"
        case "高雄市":
            return "Kaohsiung"
        case "基隆市":
            return "Keelung"
        case "新竹市":
            return "Hsinchu"
        case "嘉義市":
            return "Chiayi"
        case "新竹縣":
            return "Hsinchu County"
        case "苗栗縣":
            return "Miaoli"
        case "彰化縣":
            return "Changhua"
        case "南投縣":
            return "Nantou"
        case "雲林縣":
            return "Yunlin"
        case "嘉義縣":
            return "Chiayi County"
        case "屏東縣":
            return "Pingtung"
        case "宜蘭縣":
            return "Yilan"
        case "花蓮縣":
            return "Hualien"
        case "臺東縣" | "台東縣":
            return "Taitung"
        case "澎湖縣":
            return "Penghu"
        case "金門縣":
            return "Kinmen"
        case "連江縣":
            return "Lienchiang"
        case _:
            return ch_name  # fallback, just in case



def is_land(lat, lng):
    point = Point(lng, lat)  # Note: Point(x, y) = (lng, lat)
    return land.contains(point).any()


def get_coordinates(address):
    try:
        # Properly encode the address for URL use
        #encoded_address = urllib.parse.quote(address)

        # Your API key from Django settings
        api_key = "AIzaSyBElfTjB_ODR7adcc1xYSO1f0itjz77Lr4"

        # Construct the API URL
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

        # Make the request
        response = requests.get(url)
        data = response.json()

        # Check for valid response
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            print(f"[DEBUG] Geocoding success: {location}")
            return location['lat'], location['lng']
        else:
            print(f"[ERROR] Geocoding failed: {data['status']}")
            return None

    except Exception as e:
        print(f"[ERROR] Google Maps API request failed: {e}")
        return None
    


def score_node(node, G):
    try:
        lat, lng = G.nodes[node]['y'], G.nodes[node]['x']
        diff = calcu_next_node(lat, lng)
        score = (
            normalize(diff["congestion"]) +
            normalize(diff["elevation"]) +
            normalize(diff["road_complexity"]) +
            normalize(diff["weather_score"]) +
            normalize(diff["building_score"])
        )
        return node if score > 3.5 else None
    except Exception as e:
        print(f"[score_node] Error scoring node {node}: {e}")
        return None
    



def compute_route_segment(G, New_G, path, start_node, end_node):
    dangerous_nodes = []
    try:
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(score_node, node, G): node for node in path[1:3]}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    dangerous_nodes.append(result)
        if dangerous_nodes:
            print(f"[get_route] Rerouting around: {dangerous_nodes}")
            new_path = Short_path_Astar(G, start_node, end_node, avoid_nodes=set(dangerous_nodes))
            if new_path:
                return [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in new_path]
        return [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path]
    except Exception as e:
        print(f"[compute_route_segment] Error: {e}")
        return [(New_G.nodes[n]['y'], New_G.nodes[n]['x']) for n in path]


def get_cached_road_complexity_by_location(lat, lng):
    if road_complexity_df.empty:
        print("[RC][ERROR] road_complexity_df is empty.")
        return 0.5
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        print(f"[RC][ERROR] Invalid lat/lng values: lat={lat}, lng={lng}")
        return 0.5
    # Compute squared distance from all points
    distances = (road_complexity_df["lat"] - lat) ** 2 + (road_complexity_df["lng"] - lng) ** 2
    idx_closest = distances.idxmin()

    if pd.isna(idx_closest):
        print(f"[RC][ERROR] idxmin() failed. No closest point found.")
        return 0.5

    cand_value = road_complexity_df.loc[idx_closest]["road_complexity"]
    print(f"[RC][SUCCESS] Closest road complexity for ({lat}, {lng}) is {cand_value}")
    return cand_value
