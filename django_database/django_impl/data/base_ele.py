import requests
import time
import numpy as np
import pandas as pd

# Define city bounds (min_lat, max_lat, min_lng, max_lng)
city_bounds = {
    "台北市": (25.00, 25.13, 121.45, 121.62),
    "新北市": (24.90, 25.30, 121.30, 121.80),
    "基隆市": (25.05, 25.20, 121.65, 121.80),
    "桃園市": (24.80, 25.10, 121.10, 121.40),
    "新竹市": (24.75, 24.85, 120.90, 121.00),
    "新竹縣": (24.60, 24.90, 120.85, 121.20),
    "苗栗縣": (24.30, 24.70, 120.70, 121.00),
    "台中市": (24.00, 24.30, 120.50, 120.80),
    "彰化縣": (23.80, 24.20, 120.30, 120.60),
    "南投縣": (23.70, 24.20, 120.70, 121.10),
    "雲林縣": (23.60, 23.90, 120.20, 120.60),
    "嘉義市": (23.40, 23.55, 120.40, 120.50),
    "嘉義縣": (23.30, 23.60, 120.10, 120.50),
    "台南市": (22.85, 23.15, 120.10, 120.35),
    "高雄市": (22.50, 22.80, 120.20, 120.45),
    "屏東縣": (22.30, 22.80, 120.45, 120.85),
    "宜蘭縣": (24.50, 24.85, 121.60, 121.90),
    "花蓮縣": (23.70, 24.10, 121.30, 121.70),
    "台東縣": (22.50, 23.10, 121.00, 121.50),
    "澎湖縣": (23.50, 23.65, 119.50, 119.65)
}

def sample_grid(min_lat, max_lat, min_lng, max_lng, step=0.05):
    lat_points = list(np.arange(min_lat, max_lat, step))
    lng_points = list(np.arange(min_lng, max_lng, step))
    return [(lat, lng) for lat in lat_points for lng in lng_points]

def get_avg_elevation(points):
    elevations = []
    for batch_start in range(0, len(points), 100):
        batch = points[batch_start:batch_start + 100]
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in batch])
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations_str}"
        try:
            response = requests.get(url)
            results = response.json()["results"]
            elevations += [res["elevation"] for res in results]
        except Exception as e:
            print(f"Error in elevation API: {e}")
        time.sleep(1.2)  # avoid rate limit
    return round(np.mean(elevations), 2) if elevations else None

results = []
for city, (min_lat, max_lat, min_lng, max_lng) in city_bounds.items():
    print(f"Processing {city}...")
    points = sample_grid(min_lat, max_lat, min_lng, max_lng)
    avg_elevation = get_avg_elevation(points)
    results.append({"city": city, "avg_elevation_m": avg_elevation})

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("taiwan_city_average_elevations.csv", index=False)
print("Saved to taiwan_city_average_elevations.csv")
