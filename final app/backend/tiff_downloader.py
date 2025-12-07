# ndwi_tiff_downloader_exact_like_your_rgb.py
import os
import json
import requests
import traceback
from datetime import datetime, timedelta
from dateutil.parser import parse
from pyproj import Geod
from PIL import Image
import io
import math
import time

# ---------------- BBOX TO PIXELS (exact same as your RGB script) ----------------
def bbox_to_pixels(bbox, resolution=10):
    geod = Geod(ellps="WGS84")
    min_lon, min_lat, max_lon, max_lat = bbox
    _, _, width_m = geod.inv(min_lon, (min_lat + max_lat) / 2,
                             max_lon, (min_lat + max_lat) / 2)
    _, _, height_m = geod.inv((min_lon + max_lon) / 2, min_lat,
                             (min_lon + max_lon) / 2, max_lat)
    return math.ceil(width_m / resolution), math.ceil(height_m / resolution)

# ---------------- CONFIG & TOKEN (unchanged) ----------------
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
        r = requests.post(url, data=data, timeout=60)
        r.raise_for_status()
        token_data = r.json()
        token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600) - 60
        return token_data
    except Exception as e:
        print(f"Token request failed: {e}")
        raise

# ---------------- EXACT SAME SCENE SEARCH AS YOUR RGB DOWNLOADER ----------------
def find_closest_scene(target_date, bbox, token_data, cfg, search_window_days=120):
    if datetime.now().timestamp() > token_data["expires_at"]:
        print("Token expired → refreshing")
        token_data = get_token(cfg["username"], cfg["password"])

    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    minx, miny, maxx, maxy = bbox

    start = (target_date - timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end   = (target_date + timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Try STAC first (same as RGB)
    items = []
    url = "https://stac.dataspace.copernicus.eu/v1/search"
    payload = {
        "collections": ["SENTINEL2_L2A"],
        "bbox": [minx, miny, maxx, maxy],
        "datetime": f"{start}/{end}",
        "filter": {"op": "<", "args": [{"property": "eo:cloud_cover"}, cfg.get("max_cloud_coverage", 100)]},
        "limit": 20
    }
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code in [400, 503]:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            items = r.json().get("features", [])
            break
        except:
            time.sleep(2 ** attempt)

    # OpenSearch fallback (same as RGB)
    if not items:
        opensearch_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"
        params = {
            "box": f"{minx},{miny},{maxx},{maxy}",
            "startDate": start[:10],
            "completionDate": end[:10],
            "cloudCover": f"[0,{cfg.get('max_cloud_coverage', 100)}]",
            "productType": "S2MSI2A",
            "maxRecords": 50
        }
        try:
            r = requests.get(opensearch_url, headers=headers, params=params, timeout=60)
            r.raise_for_status()
            items = r.json().get("features", [])
        except Exception as e:
            print(f"OpenSearch failed: {e}")

    if not items:
        print(f"No scene found for {target_date}")
        return None

    best = None
    best_diff = float('inf')
    for s in items:
        dt_str = s["properties"].get("datetime") or s["properties"].get("startDate")
        if not dt_str: continue
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

# ---------------- DOWNLOAD NDWI GEOTIFF (only difference from RGB) ----------------
def download_ndwi_tiff(scene, bbox, token, target_date, folder):
    try:
        dt_str = scene["properties"].get("datetime") or scene["properties"].get("startDate")
        scene_date = parse(dt_str).date()
        time_interval = (f"{scene_date}T00:00:00Z", f"{scene_date}T23:59:59Z")

        width, height = bbox_to_pixels(bbox)
        # scale_factor = 100000  # try increasing/decreasing this
    
        # xwidth=(bbox[2] - bbox[0])
        # yheight=(bbox[3] - bbox[1])
        
        # rratio=xwidth/yheight

        # width = int(xwidth * scale_factor)
        # height = int(yheight * scale_factor)
        
        # width = min(1300, width)
        # height = min(int(1300/rratio), height)
        
        
        # print(width)
        # print(height)
        print(f"Output size: {width}×{height} px")

        ndwi_evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B03","B04","B08","B11","SCL"],
                output: {bands: 5, sampleType: "FLOAT32"}
            };
        }
        function evaluatePixel(s) {
            return [s.B03, s.B04, s.B08, s.B11, s.SCL];
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
            "evalscript": ndwi_evalscript
        }

        r = requests.post(
            "https://sh.dataspace.copernicus.eu/api/v1/process",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=120
        )
        r.raise_for_status()

        # Save as real GeoTIFF
        filename = f"NDWI_5band_{scene_date}.tif"
        path = os.path.join(folder, filename)
        with open(path, "wb") as f:
            f.write(r.content)

        print(f"SAVED GeoTIFF → {path}\n")

    except Exception as e:
        print("Download failed:", e)
        traceback.print_exc()

# ---------------- EXACT SAME MAIN LOOP AS YOUR RGB SCRIPT ----------------
def download_ndwi_period():
    cfg = load_config("config3.json")

    # Token with retry
    token_data = None
    for attempt in range(10):
        try:
            print(f"Getting token... (attempt {attempt+1}/10)")
            token_data = get_token(cfg["username"], cfg["password"])
            print("Token OK!\n")
            break
        except:
            time.sleep(15)
    if not token_data:
        print("Failed to get token.")
        return

    bbox = cfg["bbox"]
    folder = cfg.get("download_folder", "ndwi_geotiffs")
    os.makedirs(folder, exist_ok=True)

    start_date = datetime(2020, 1, 1).date()
    end_date   = datetime(2025, 1, 2).date()
    current = start_date

    print(f"Starting NDWI GeoTIFF download (June–Sep 2025)\n")

    while current <= end_date:
        target_date = current
        current += timedelta(days=1800)

        print(f"\nDownloading NDWI for target date: {target_date}")
        print(f"BBox: {bbox}\n")

        scene = find_closest_scene(target_date, bbox, token_data, cfg)
        if not scene:
            print("No scene found → skipping\n")
            continue

        download_ndwi_tiff(scene, bbox, token_data["access_token"], target_date, folder)

    print("All done! Check your folder.")

# ---------------- RUN ----------------
if __name__ == "__main__":
    download_ndwi_period()