# monthly_rgb_downloader_from_your_working_script.py
import os
import json
import requests
import traceback
from datetime import datetime, timedelta
from dateutil.parser import parse
from pyproj import Geod
from PIL import Image
import numpy as np
import time
import io
import math

def bbox_to_pixels(bbox, resolution=10):
    """
    Convert a WGS84 bounding box to pixel dimensions based on ground resolution.

    bbox = [min_lon, min_lat, max_lon, max_lat]
    resolution = meters per pixel (Sentinel-2 RGB = 10m)
    """
    geod = Geod(ellps="WGS84")
    min_lon, min_lat, max_lon, max_lat = bbox

    # Width: east-west distance at center latitude
    _, _, width_m = geod.inv(min_lon, (min_lat + max_lat) / 2, 
                             max_lon, (min_lat + max_lat) / 2)

    # Height: north-south distance at center longitude
    _, _, height_m = geod.inv((min_lon + max_lon) / 2, min_lat,
                              (min_lon + max_lon) / 2, max_lat)

    width_px  = math.ceil(width_m  / resolution)
    height_px = math.ceil(height_m / resolution)

    return width_px, height_px

# ---------------- CONFIG (use your existing config2.json) ----------------
def load_config(path="config3.json"):
    with open(path) as f:
        return json.load(f)

def get_token(username, password):
    url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    try:
        r = requests.post(url, data=data)
        r.raise_for_status()
        token_data = r.json()
        token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600)
        return token_data
    except Exception as e:
        print(f"Token request failed: {e}")
        raise

# ---------------- YOUR ORIGINAL WORKING SCENE SEARCH (unchanged) ----------------
def find_closest_scene(target_date, bbox, token_data, cfg, search_window_days=12):
    token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    start = (target_date - timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (target_date + timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    minx, miny, maxx, maxy = bbox

    # Try STAC first (even with broken filter — we have fallback)
    payload = {
        "collections": ["SENTINEL2_L2A"],
        "bbox": [minx, miny, maxx, maxy],
        "datetime": f"{start}/{end}",
        "filter": {
            "op": "<",
            "args": [{"property": "eo:cloud_cover"}, cfg.get("max_cloud_coverage", 20)]
        },
        "limit": 20
    }
    items = []
    url = "https://stac.dataspace.copernicus.eu/v1/search"
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code in [400, 503]:
                time.sleep(2 ** attempt)
                if datetime.now().timestamp() > token_data["expires_at"]:
                    token_data = get_token(cfg["username"], cfg["password"])
                    headers["Authorization"] = f"Bearer {token_data['access_token']}"
                continue
            r.raise_for_status()
            items = r.json().get("features", [])
            break
        except:
            time.sleep(2 ** attempt)

    # OpenSearch fallback — this is why your original script never fails
    if not items:
        opensearch_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"
        params = {
            "box": f"{minx},{miny},{maxx},{maxy}",
            "startDate": start[:10],
            "completionDate": end[:10],
            "cloudCover": "[0,20]",
            "productType": "S2MSI2A",
            "maxRecords": 50
        }
        try:
            r = requests.get(opensearch_url, headers=headers, params=params)
            r.raise_for_status()
            items = r.json().get("features", [])
        except Exception as e:
            print(f"OpenSearch failed: {e}")

    if not items:
        print(f"No scene found for {target_date}")
        return 

    # Pick closest by date
    best = None
    best_diff = float('inf')
    for s in items:
        dt_str = s["properties"].get("datetime") or s["properties"].get("startDate")
        if not dt_str:
            continue
        try:
            sd = parse(dt_str.split("T")[0]) if "T" in dt_str else parse(dt_str)
        except:
            continue
        diff = abs((sd.date() - target_date).days)
        if diff < best_diff:
            best_diff = diff
            best = s

    if best:
        actual = parse(best["properties"].get("datetime") or best["properties"].get("startDate")).date()
        print(f"Selected {best['id']} → {actual} (±{best_diff}d)")
        return best
    return None

# ---------------- PROCESS RGB ONLY ----------------
def download_rgb_only(scene, bbox, token, target_date, folder):
    try:
        dt_str = scene["properties"].get("datetime") or scene["properties"].get("startDate")
        scene_date = parse(dt_str).date()
        time_interval = (f"{scene_date}T00:00:00Z", f"{scene_date}T23:59:59Z")

        # Same size logic as your working script
        # width, height = bbox_to_pixels(bbox)
        scale_factor = 100000  # try increasing/decreasing this
    
        xwidth=(bbox[2] - bbox[0])
        yheight=(bbox[3] - bbox[1])
        
        rratio=xwidth/yheight

        width = int(xwidth * scale_factor)
        height = int(yheight * scale_factor)
        
        width = min(1300, width)
        height = min(int(1300/rratio), height)
        
        
        print(width)
        print(height)

        evalscript = """
        //VERSION=3
        function setup() {
            return { input:["B04","B03","B02"], output:{bands:3,sampleType:"UINT8"} };
        }
        function evaluatePixel(s) {
            return [Math.min(1,s.B04*2.5)*255, Math.min(1,s.B03*2.5)*255, Math.min(1,s.B02*2.5)*255];
        }
        """

        payload = {
            "input": {
                "bounds": {"bbox": bbox},
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {"timeRange": {"from": time_interval[0], "to": time_interval[1]}}
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
            },
            "evalscript": evalscript
        }

        r = requests.post(
            "https://sh.dataspace.copernicus.eu/api/v1/process",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=90
        )
        r.raise_for_status()

        # Save as JPG
        filename = f"RGB_{scene_date}.jpg"
        path = os.path.join(folder, filename)
        Image.open(io.BytesIO(r.content)).convert("RGB").save(path, "JPEG", quality=95)
        print(f"SAVED → {path}\n")

    except Exception as e:
        print("Download failed:", e)
        traceback.print_exc()

# ---------------- MAIN: Monthly RGB Downloader ----------------
# ---------------- JUST ONE DATE TEST ----------------
def download_one_rgb_image():
    cfg = load_config("config3.json")
    
    # Refresh token with retry (so you never get timeout again)
    token_data = None
    for attempt in range(10):
        try:
            print(f"Getting token... (attempt {attempt+1}/10)")
            token_data = get_token(cfg["username"], cfg["password"])
            print("Token OK!")
            break
        except:
            time.sleep(15)
    if not token_data:
        print("Could not get token. Check internet or wait 5 mins.")
        return

    bbox = cfg["bbox"]
    folder = cfg.get("download_folder", "monthly_rgb")
    os.makedirs(folder, exist_ok=True)

    # CHANGE THIS DATE TO WHATEVER YOU WANT TO TEST
    # target_date = datetime(2024, 11, 1).date()   # ← June 5, 2023 (usually has good clear images)

    # print(f"\nDownloading RGB for target date: {target_date}")
    # print(f"BBox: {bbox}\n")

    # scene = find_closest_scene(target_date, bbox, token_data, cfg)
    # if not scene:
    #     print("No scene found for this date.")
    #     return
    

    start_date = datetime(2016, 1, 1).date()
    end_date   = datetime(2025, 1, 1).date()
    # end_date   = start_date

    current = start_date
    while current <= end_date:
        
        target_date = current 
        current += timedelta(days=15)
        print(f"\nDownloading RGB for target date: {target_date}")
        print(f"BBox: {bbox}\n")

        scene = find_closest_scene(target_date, bbox, token_data, cfg)
        if not scene:
            print("No scene found for this date.")
            current += timedelta(days=15)
            continue
        download_rgb_only(scene, bbox, token_data["access_token"], target_date, folder)
        print("DONE! Check your folder.")  
        


# ---------------- RUN ONLY ONE IMAGE ----------------
if __name__ == "__main__":
    download_one_rgb_image()