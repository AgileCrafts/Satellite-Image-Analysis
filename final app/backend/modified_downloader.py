import io
import json
import requests
import traceback
from datetime import datetime, timedelta
import tifffile
import time
from sqlalchemy.orm import Session
from models import Image
from database import SessionLocal
from geoalchemy2.shape import to_shape
import math
from PIL import Image as PILImage
import os
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import from_bounds


from pyproj import Geod
import math
from pyproj import Proj, transform

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


# def bbox_to_pixels(bbox, resolution=10):
#     geod = Geod(ellps="WGS84")
#     minx, miny, maxx, maxy = bbox

#     # WGS84 to Web Mercator (EPSG:3857)
#     wgs84 = Proj(init='epsg:4326')  # WGS84
#     mercator = Proj(init='epsg:3857')  # Web Mercator
    
#     # Convert bounding box corners to Web Mercator
#     minx_merc, miny_merc = transform(wgs84, mercator, minx, miny)
#     maxx_merc, maxy_merc = transform(wgs84, mercator, maxx, maxy)

#     # Now, calculate the width and height in Web Mercator
#     width_m = maxx_merc - minx_merc
#     height_m = maxy_merc - miny_merc

#     return (
#         math.ceil(width_m / resolution),
#         math.ceil(height_m / resolution)
#     )



# def fix_transform(tiff_bytes, bbox, width, height):
#     """
#     Correctly set transform for Mapbox: top-left origin, negative Y pixel size.
#     """
#     minx, miny, maxx, maxy = bbox
    
#     # Calculate pixel sizes
#     pixel_x = (maxx - minx) / width
#     pixel_y = (miny - maxy) / height  # negative because top to bottom
    
#     # Top-left corner as origin
#     transform = rasterio.Affine(
#         pixel_x, 0.0, minx,
#         0.0, pixel_y, maxy
#     )
    
#     with MemoryFile(tiff_bytes) as memfile:
#         with memfile.open() as src:
#             profile = src.profile.copy()
#             profile.update({
#                 "crs": "EPSG:4326",
#                 "transform": transform,
#                 "width": width,
#                 "height": height
#             })
#             data = src.read()
#             with MemoryFile() as out_mem:
#                 with out_mem.open(**profile) as dst:
#                     dst.write(data)
#                 return out_mem.getvalue()


# # ---------------- TIFF REPROJECT FIX ----------------
# def reproject_tiff_to_4326(tiff_bytes: bytes) -> bytes:
#     """
#     Ensures TIFF is EPSG:4326.
#     Returns new TIFF bytes.
#     """
#     with MemoryFile(tiff_bytes) as memfile:
#         with memfile.open() as src:

#             if src.crs and src.crs.to_string() == "EPSG:4326":
#                 return tiff_bytes  # already correct

#             dst_crs = "EPSG:4326"
#             transform, width, height = calculate_default_transform(
#                 src.crs, dst_crs, src.width, src.height, *src.bounds
#             )

#             profile = src.profile.copy()
#             profile.update({
#                 "crs": dst_crs,
#                 "transform": transform,
#                 "width": width,
#                 "height": height
#             })

#             with MemoryFile() as out_mem:
#                 with out_mem.open(**profile) as dst:
#                     for i in range(1, src.count + 1):
#                         reproject(
#                             source=rasterio.band(src, i),
#                             destination=rasterio.band(dst, i),
#                             src_transform=src.transform,
#                             src_crs=src.crs,
#                             dst_transform=transform,
#                             dst_crs=dst_crs,
#                             resampling=Resampling.nearest
#                         )
#                 return out_mem.getvalue()

def reproject_tiff_to_3857(tiff_bytes: bytes, bbox: list) -> bytes:
    """
    Reproject TIFF to EPSG:3857 (Web Mercator) for Mapbox compatibility.
    Returns new TIFF bytes.
    """
    src_crs = "EPSG:4326"  # Assuming input is 4326 as per your script
    dst_crs = "EPSG:3857"

    with MemoryFile(tiff_bytes) as memfile:
        with memfile.open() as src:
            # Calculate new transform, width, height for destination CRS
            transform, width, height = calculate_default_transform(
                src.crs or src_crs,  # Use src CRS if set, else assume 4326
                dst_crs,
                src.width,
                src.height,
                *src.bounds  # Unpack original bounds
            )

            # Update profile for output
            profile = src.profile.copy()
            profile.update({
                "crs": dst_crs,
                "transform": transform,
                "width": width,
                "height": height,
                "nodata": src.nodata  # Preserve nodata if set
            })

            # Create output in memory
            with MemoryFile() as out_mem:
                with out_mem.open(**profile) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs or src_crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.bilinear  # Or nearest for categorical data like SCL
                        )
                return out_mem.read()

# ---------------- SCENE SEARCH (STAC) ----------------
def find_closest_scene(target_date, bbox, token_data, cfg, search_window_days=30):
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
def process_request(evalscript, bbox, time_interval, token):
    """Call Copernicus Processing API to get TIFF."""
    url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        # "input": {
        #     "bounds": {"bbox": bbox},
        #     "data": [{
        #         "type": "sentinel-2-l2a",
        #         "dataFilter": {"timeRange": {"from": time_interval[0], "to": time_interval[1]}}
        #     }]
        # },
        # "output": {
        #     "width": width,
        #     "height": height,
        #     "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
        # },
        "input": {
            "bounds": {
                "bbox": bbox
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": time_interval[0],
                        "to": time_interval[1]
                    }
                }
            }]
        },
        "output": {
            "resolution": [10, 10],
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/tiff"}
            }]
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
def download_scene(scene_info, cfg, bbox, token, index, port_id: int, db: Session):
    scene_id = scene_info["id"]
    time = scene_info["properties"].get("datetime") or scene_info["properties"].get("startDate")
    date_obj = parse_iso8601_utc(time)
    date_str = date_obj.date().isoformat()
    cloud_cover = scene_info["properties"].get("eo:cloud_cover") or scene_info["properties"].get("cloudCover")

    # check if already exists
    existing = db.query(Image).filter(
        Image.port_id == port_id,
        Image.image_date == date_obj.date()
    ).first()
    if existing:
        print(f"Already exists for AOI={port_id}, date={date_str}, id={existing.id}")
        return existing.id

    print(f"Downloading scene {index+1}: {scene_id} on {date_str}, cloud={cloud_cover}")

    # fixed output size
    # width=1200
    # height=512
    
    print(bbox)
    # print("\n\n\n\n\n\n\n\n")
    # width, height = bbox_to_pixels(bbox, resolution=10)
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
    # minx, miny, maxx, maxy = bbox
    # center_lat = (miny + maxy) / 2

    # scale_factor_lat = 111320 / 10  # ~11,132 pixels per degree latitude
    # scale_factor_lon = (111320 * math.cos(math.radians(center_lat))) / 10
    
    # print(scale_factor_lat)

    # width = int((maxx - minx) * scale_factor_lon)
    # height = int((maxy - miny) * scale_factor_lat)

    # width = max(1, width)
    # height = max(1, height)

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
        # Download
        # ndwi_tiff = process_request(ndwi_evalscript, bbox, time_interval, width, height, token)
        # rgb_tiff = process_request(rgb_evalscript, bbox, time_interval, width, height, token)

        ndwi_tiff = process_request(ndwi_evalscript, bbox, time_interval, token)
        rgb_tiff = process_request(rgb_evalscript, bbox, time_interval, token)

        # 🔥 FIX: REPROJECT IMMEDIATELY
        # ndwi_tiff = reproject_tiff_to_3857(ndwi_tiff, bbox)
        # rgb_tiff = reproject_tiff_to_3857(rgb_tiff, bbox)
        
        # ndwi_tiff = fix_transform(ndwi_tiff, bbox, width, height)
        # rgb_tiff = fix_transform(rgb_tiff, bbox, width, height)
        
        with MemoryFile(ndwi_tiff) as memfile:
            with memfile.open() as src:
                print("CRS:", src.crs)
                print("Transform (full precision):")
                print(repr(src.transform))  # This shows the exact Affine object with all decimals
                print("Individual values:")
                print(f"Pixel size X: {src.transform.a}")
                print(f"Pixel size Y: {src.transform.e}")
                print(f"Upper-left X: {src.transform.c}")
                print(f"Upper-left Y: {src.transform.f}")
                print("Bounds:", src.bounds)
                print("Width, Height:", src.width, src.height)

        new_image = Image(
            port_id=port_id,
            image_date=date_obj.date(),
            ndwi_data=ndwi_tiff,
            rgb_data=rgb_tiff,
            meta_data={
                "crs": "EPSG:3857",
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
def download_images(target_date, bbox, port_id):
    """
    Finds closest Sentinel-2 scene to the given date + bbox,
    downloads image, stores in DB, returns image_id.

    Params:
        target_date (datetime.date or str)
        bbox (list): [minx, miny, maxx, maxy]
        aoi_id (int | None): Optional, if you want to tag image with an AOI
    Returns:
        image_id (int) or None
    """
    cfg = load_config()
    db: Session = SessionLocal()

    try:
        # Normalize date
        if isinstance(target_date, str):
            from dateutil.parser import parse
            target_date = parse(target_date).date()

        print(f"Downloading closest image near: {target_date}, BBox={bbox}")

        token_data = get_token(cfg["username"], cfg["password"])  # returns dict with expiry

        # Find closest scene
        scene = find_closest_scene(target_date, bbox, token_data, cfg)
        if scene:
            image_id = download_scene(
                scene_info=scene,
                cfg=cfg,
                bbox=bbox,
                token=token_data["access_token"],
                index=0,
                port_id=port_id,
                db=db
            )
            
            
            if image_id:
                 # Retrieve the downloaded image record
                downloaded_image = db.query(Image).filter_by(id=image_id).first()
                if downloaded_image:
                    # Convert RGB TIFF to JPG and save (optional)
                    rgb_tiff_data = downloaded_image.rgb_data
                    rgb_image = PILImage.open(io.BytesIO(rgb_tiff_data))
                    os.makedirs("images", exist_ok=True)
                    rgb_filename = f"images/{port_id}_{target_date}_rgb.jpg"
                    rgb_image.save(rgb_filename, "JPEG")
                    print(f"Saved RGB image: {rgb_filename}")
                    
                    # Return NDWI raw bytes for further processing
                    db.commit()
                    print(f"Downloaded image ID={image_id}")
                    return downloaded_image.ndwi_data

        else:
            print(f"No scene found near {target_date}")
            return None

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        db.rollback()
        return None

    finally:
        db.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    bbox = [90.50183061170463, 23.564356390973032, 90.53536605820631, 23.579282107830622]
    date = "2024-01-21"
    port_id = 1  # optional

    image_id = download_images(date, bbox, port_id)
    print("Downloaded image ID:", image_id)