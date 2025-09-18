import io
import json
import numpy as np
import traceback
from datetime import datetime, timedelta
import tifffile

from sentinelhub import (
    SHConfig, BBox, CRS, SentinelHubCatalog, DataCollection,
    SentinelHubRequest, MimeType, bbox_to_dimensions
)
from sqlalchemy.orm import Session
from models import Image, AOI, ChangeMap   # <- make sure models.py uses the same Base/engine
from database import SessionLocal           # <- must be your DB session factory
from geoalchemy2.shape import to_shape

# Load SentinelHub credentials and settings
def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)

def parse_iso8601_utc(date_str):
    if date_str.endswith("Z"):
        date_str = date_str[:-1]
    return datetime.fromisoformat(date_str)

def find_closest_scene(target_date, bbox, sh_config, cfg, search_window_days=120):
    """Search catalog for the Sentinel-2 scene closest to target_date within +/- search_window_days.
       Returns the scene_info dict or None.
    """
    print(f"Searching scenes within ±{search_window_days} days for {target_date.isoformat()} ...")
    catalog = SentinelHubCatalog(config=sh_config)

    start = (target_date - timedelta(days=search_window_days)).isoformat()
    end = (target_date + timedelta(days=search_window_days)).isoformat()

    try:
        search_iterator = catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=bbox,
            time=(start, end),
            filter=f"eo:cloud_cover < {cfg.get('max_cloud_coverage', 100)}"
        )
        results = list(search_iterator)
    except Exception as e:
        print("Catalog search failed:", e)
        traceback.print_exc()
        return None

    if not results:
        print("No results found in catalog search.")
        return None

    # compute actual capture datetime for each result and pick the closest
    def scene_date(scene):
        t = scene.get("properties", {}).get("datetime")
        if not t:
            return None
        try:
            return parse_iso8601_utc(t)
        except Exception:
            return None

    best = None
    best_diff = None
    for s in results:
        sd = scene_date(s)
        if sd is None:
            continue
        diff = abs((sd.date() - target_date).days)
        if best is None or diff < best_diff:
            best = s
            best_diff = diff

    if best:
        print(f"Picked scene {best.get('id')} (date {best.get('properties', {}).get('datetime')}) diff {best_diff} days")
    else:
        print("No scene with valid datetime found in results.")

    return best

def download_scene(scene_info, cfg, bbox, config, index, aoi_id: int, db: Session):
    scene_id = scene_info["id"]
    time = scene_info["properties"]["datetime"]
    date_obj = parse_iso8601_utc(time)
    date_str = date_obj.date().isoformat()
    cloud_cover = scene_info["properties"].get("eo:cloud_cover", None)
    
    # --- Check if already exists ---
    existing = db.query(Image).filter(
        Image.aoi_id == aoi_id,
        Image.image_date == date_obj.date()
    ).first()

    if existing:
        print(f"Image already exists for AOI={aoi_id}, date={date_str}, reusing id={existing.id}")
        return existing.id

    print(f"Downloading scene {index+1}: {scene_id} captured on {date_str}, cloud={cloud_cover}")

    size = bbox_to_dimensions(bbox, resolution=cfg["resolution"])
    time_interval = (f"{date_str}T00:00:00", f"{date_str}T23:59:59")

    # --- NDWI TIFF evalscript ---
    ndwi_evalscript = """
    //VERSION=3
    function setup() {
        return { input: ["B03","B04","B08","B11","SCL"], output:{bands:5,sampleType:"FLOAT32"}};
    }
    function evaluatePixel(sample) { return [sample.B03,sample.B04,sample.B08,sample.B11,sample.SCL]; }
    """

    # --- RGB evalscript ---
    rgb_evalscript = """
    //VERSION=3
    function setup() {
        return { input:["B04","B03","B02"], output:{bands:3,sampleType:"UINT8"} };
    }
    function evaluatePixel(sample) {
        return [
            Math.min(1, sample.B04*2.5)*255,
            Math.min(1, sample.B03*2.5)*255,
            Math.min(1, sample.B02*2.5)*255
        ];
    }
    """

    # --- Request NDWI TIFF ---
    ndwi_request = SentinelHubRequest(
        evalscript=ndwi_evalscript,
        input_data=[SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,
            time_interval=time_interval,
        )],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )
    ndwi_img = ndwi_request.get_data()[0]
    if np.mean(ndwi_img==0) > 0.2:
        print(f"Skipped scene {index+1}: too much black area")
        return None
    ndwi_buf = io.BytesIO()
    tifffile.imwrite(ndwi_buf, ndwi_img)
    ndwi_buf.seek(0)

    # --- Request RGB TIFF ---
    rgb_request = SentinelHubRequest(
        evalscript=rgb_evalscript,
        input_data=[SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,
            time_interval=time_interval,
        )],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config,
    )
    rgb_img = rgb_request.get_data()[0]
    rgb_buf = io.BytesIO()
    tifffile.imwrite(rgb_buf, rgb_img)
    rgb_buf.seek(0)

    # --- Metadata ---
    meta_data = {
        "scene_id": scene_id,
        "capture_date": date_str,
        "cloud_cover": cloud_cover,
        "aoi_id": aoi_id,
        "bands": ["B03","B04","B08","B11","SCL"],
        "resolution": cfg["resolution"]
    }

    # --- Insert into DB ---
    new_image = Image(
        aoi_id=aoi_id,
        image_date=date_obj.date(),
        ndwi_data=ndwi_buf.read(),
        rgb_data=rgb_buf.read(),
        meta_data=meta_data
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    print(f"Inserted into DB id={new_image.id}, date={date_str}")
    return new_image.id



def download_change_map_images(change_map_id: int):
    cfg = load_config()
    db: Session = SessionLocal()
    try:
        change_map = db.query(ChangeMap).filter(ChangeMap.id == change_map_id).first()
        if not change_map:
            print(f"No ChangeMap found with id={change_map_id}")
            return

        from_date = change_map.from_date
        to_date = change_map.to_date
        aoi_id = change_map.aoi_id

        if not from_date or not to_date:
            print("ChangeMap lacks from_date or to_date")
            return

        aoi = db.query(AOI).filter(AOI.id == aoi_id).first()
        if not aoi:
            print("AOI not found:", aoi_id)
            return
        if not aoi.geom:
            print("AOI has no stored geometry (geom is NULL).")
            return

        geom_shape = to_shape(aoi.geom)
        minx, miny, maxx, maxy = geom_shape.bounds
        bbox = BBox([minx, miny, maxx, maxy], crs=CRS.WGS84)

        sh_config = SHConfig()
        sh_config.sh_client_id = cfg["sh_client_id"]
        sh_config.sh_client_secret = cfg["sh_client_secret"]

        # Pre-image
        pre_scene = find_closest_scene(from_date, bbox, sh_config, cfg)
        if pre_scene:
            pre_image_id = download_scene(pre_scene, cfg, bbox, sh_config, 0, aoi_id, db)
            if pre_image_id:
                change_map.pre_image_id = pre_image_id
        else:
            print("No pre-scene found near", from_date)

        # Post-image
        post_scene = find_closest_scene(to_date, bbox, sh_config, cfg)
        if post_scene:
            post_image_id = download_scene(post_scene, cfg, bbox, sh_config, 1, aoi_id, db)
            if post_image_id:
                change_map.post_image_id = post_image_id
        else:
            print("No post-scene found near", to_date)

        db.commit()
        
        print(f"Assigned pre_image_id: {change_map.pre_image_id}")
        print(f"Assigned post_image_id: {change_map.post_image_id}")

        print(f"ChangeMap images updated for id={change_map_id} (pre={change_map.pre_image_id}, post={change_map.post_image_id})")

    except Exception as e:
        print(f"Error in download_change_map_images: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


