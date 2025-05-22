import os
import pickle
import threading

from django.conf import settings

import osmnx as ox
_graph_cache = None
_graph_lock = threading.Lock()
_graph_loaded = threading.Event()

def load_graph_once():
    graph_dir = os.path.join(r'C:\Users\Brian\UberApp\Djangle_test\DB_project\django_database\django_impl', 'osm')
    #graph_path = os.path.join(graph_dir, 'taiwan_drive.graphml')
    gpickle_path = os.path.join(graph_dir, 'taiwan_drive.gpickle')
    #print(graph_path)
    global _graph_cache
    with _graph_lock:
        if _graph_cache is None:
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
            _graph_loaded.set()
        return _graph_cache
    
print("downloading")
G = load_graph_once()
print(type(G))