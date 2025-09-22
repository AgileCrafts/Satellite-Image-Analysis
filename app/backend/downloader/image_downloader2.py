import io
import json
import requests
import traceback
from datetime import datetime, timedelta
import tifffile
import time
from sqlalchemy.orm import Session
from models import Image, AOI, ChangeMap
from database import SessionLocal
from geoalchemy2.shape import to_shape

# ---------------- CONFIG ----------------
def load_config(path="config2.json"):
    with open(path) as f:
        return json.load(f)

def get_token(username, password):
    """Get OAuth2 token from Copernicus Data Space."""
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

def parse_iso8601_utc(date_str):
    if date_str.endswith("Z"):
        date_str = date_str[:-1]
    return datetime.fromisoformat(date_str)

# ---------------- SCENE SEARCH (STAC) ----------------
def find_closest_scene(target_date, bbox, token_data, cfg, search_window_days=120):
    """
    Search for the closest Sentinel-2 L2A scene using CDSE STAC API with fallback to OpenSearch.
    Returns the scene dictionary or None if not found.
    """
    token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # print(headers)

    # Format datetime properly for STAC
    start = (target_date - timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (target_date + timedelta(days=search_window_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Validate bbox
    minx, miny, maxx, maxy = bbox
    if minx > maxx or miny > maxy:
        print(f"Invalid bbox: {bbox}. Ensure minx ≤ maxx, miny ≤ maxy.")
        return None

    # STAC payload with filter and limit
    payload = {
        "collections": ["SENTINEL2_L2A"],
        "bbox": [minx, miny, maxx, maxy],
        "datetime": f"{start}/{end}",
        "filter": {
            "op": "<",
            "args": [{"property": "eo:cloud_cover"}, cfg.get("max_cloud_coverage", 100)]
        },
        "limit": 20
    }

    # Initialize items to avoid UnboundLocalError
    items = []
    url = "https://stac.dataspace.copernicus.eu/v1/search"

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code in [400, 503]:
                print(f"[Run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] STAC error {r.status_code} (attempt {attempt+1}/3): {r.text}")
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                if datetime.now().timestamp() > token_data["expires_at"]:
                    print("Token expired, refreshing...")
                    token_data = get_token(cfg["username"], cfg["password"])
                    token = token_data["access_token"]
                    headers["Authorization"] = f"Bearer {token}"
                continue
            r.raise_for_status()
            items = r.json().get("features", [])
            break
        except requests.exceptions.RequestException as e:
            print(f"[Run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] STAC request failed (attempt {attempt+1}): {e}")
            if attempt == 2:
                print("Falling back to OpenSearch API...")
                break
            time.sleep(2 ** attempt)

    if not items:
        # Fallback: OpenSearch API
        opensearch_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"
        params = {
            "box": f"{minx},{miny},{maxx},{maxy}",
            "startDate": start[:10],
            "completionDate": end[:10],
            "cloudCover": f"[0,{cfg.get('max_cloud_coverage', 100)}]",
            "productType": "S2MSI2A",
            "maxRecords": 20
        }
        try:
            r = requests.get(opensearch_url, headers=headers, params=params)
            r.raise_for_status()
            items = r.json().get("features", [])
        except Exception as e:
            print(f"OpenSearch fallback failed: {e}")
            return None

    if not items:
        print(f"No results found in catalog search for date {target_date}")
        return None

    # Pick the closest scene by date
    best_scene = None
    best_diff = None
    for s in items:
        dt_str = s["properties"].get("datetime") or s["properties"].get("startDate")
        if not dt_str:
            continue
        sd = parse_iso8601_utc(dt_str)
        diff_days = abs((sd.date() - target_date).days)
        if best_scene is None or diff_days < best_diff:
            best_scene = s
            best_diff = diff_days

    if best_scene:
        print(f"Picked scene {best_scene['id']} at {best_scene['properties'].get('datetime', best_scene['properties'].get('startDate'))} (diff {best_diff} days)")
    else:
        print("No suitable scene found.")
    return best_scene

# ---------------- PROCESSING API ----------------
def process_request(evalscript, bbox, time_interval, width, height, token):
    """Call Copernicus Processing API to get TIFF."""
    url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    headers = {"Authorization": f"Bearer {token}"}

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

    try:
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"Process API failed: {e}")
        raise

# ---------------- DOWNLOAD SCENE ----------------
def download_scene(scene_info, cfg, bbox, token, index, aoi_id: int, db: Session):
    scene_id = scene_info["id"]
    time = scene_info["properties"].get("datetime") or scene_info["properties"].get("startDate")
    date_obj = parse_iso8601_utc(time)
    date_str = date_obj.date().isoformat()
    cloud_cover = scene_info["properties"].get("eo:cloud_cover") or scene_info["properties"].get("cloudCover")

    # check if already exists
    existing = db.query(Image).filter(
        Image.aoi_id == aoi_id,
        Image.image_date == date_obj.date()
    ).first()
    if existing:
        print(f"Already exists for AOI={aoi_id}, date={date_str}, id={existing.id}")
        return existing.id

    print(f"Downloading scene {index+1}: {scene_id} on {date_str}, cloud={cloud_cover}")

    # fixed output size
    width, height = 512, 512
    time_interval = (f"{date_str}T00:00:00Z", f"{date_str}T23:59:59Z")

    # NDWI evalscript
    ndwi_evalscript = """
    //VERSION=3
    function setup() {
        return { input: ["B03","B04","B08","B11","SCL"], output:{bands:5,sampleType:"FLOAT32"}};
    }
    function evaluatePixel(s) { return [s.B03,s.B04,s.B08,s.B11,s.SCL]; }
    """

    # RGB evalscript
    rgb_evalscript = """
    //VERSION=3
    function setup() {
        return { input:["B04","B03","B02"], output:{bands:3,sampleType:"UINT8"} };
    }
    function evaluatePixel(s) {
        return [Math.min(1,s.B04*2.5)*255, Math.min(1,s.B03*2.5)*255, Math.min(1,s.B02*2.5)*255];
    }
    """

    try:
        ndwi_tiff = process_request(ndwi_evalscript, bbox, time_interval, width, height, token)
        rgb_tiff = process_request(rgb_evalscript, bbox, time_interval, width, height, token)

        new_image = Image(
            aoi_id=aoi_id,
            image_date=date_obj.date(),
            ndwi_data=ndwi_tiff,
            rgb_data=rgb_tiff,
            meta_data={
                "scene_id": scene_id,
                "capture_date": date_str,
                "cloud_cover": cloud_cover,
                "bands": ["B03","B04","B08","B11","SCL"],
                "resolution": cfg["resolution"]
            }
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        print(f"Inserted DB id={new_image.id}, date={date_str}")
        return new_image.id
    except Exception as e:
        print("Download failed:", e)
        traceback.print_exc()
        return None

# ---------------- MAIN ----------------
def another_download_change_map_images(change_map_id: int):
    cfg = load_config()
    db: Session = SessionLocal()

    try:
        change_map = db.query(ChangeMap).filter(ChangeMap.id == change_map_id).first()
        if not change_map:
            print(f"No ChangeMap found with id={change_map_id}")
            return

        from_date, to_date, aoi_id = change_map.from_date, change_map.to_date, change_map.aoi_id
        aoi = db.query(AOI).filter(AOI.id == aoi_id).first()
        if not aoi or not aoi.geom:
            print("AOI not found or empty geometry")
            return
        geom_shape = to_shape(aoi.geom)
        minx, miny, maxx, maxy = geom_shape.bounds
        bbox = [minx, miny, maxx, maxy]
        print(f"ChangeMap {change_map_id}: From={from_date}, To={to_date}, BBox={bbox}")  # Debug

        token_data = get_token(cfg["username"], cfg["password"])  # Now returns dict with expiry

        # Pre-image
        pre_scene = find_closest_scene(from_date, bbox, token_data, cfg)
        if pre_scene:
            change_map.pre_image_id = download_scene(pre_scene, cfg, bbox, token_data["access_token"], 0, aoi_id, db)
        else:
            print("No pre-scene found near", from_date)

        # Post-image
        post_scene = find_closest_scene(to_date, bbox, token_data, cfg)
        if post_scene:
            change_map.post_image_id = download_scene(post_scene, cfg, bbox, token_data["access_token"], 1, aoi_id, db)
        else:
            print("No post-scene found near", to_date)

        db.commit()
        print(f"Updated ChangeMap {change_map_id} → pre={change_map.pre_image_id}, post={change_map.post_image_id}")

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    another_download_change_map_images(25)