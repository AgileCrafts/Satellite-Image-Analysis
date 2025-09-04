import os
import json
from sentinelhub import (
    SHConfig, BBox, CRS, SentinelHubCatalog, DataCollection,
    SentinelHubRequest, MimeType, bbox_to_dimensions
)
import numpy as np
from datetime import datetime
import tifffile
import traceback # <--- ADD THIS IMPORT


def load_config():
    with open('config/config.json') as f:
        return json.load(f)


def get_bbox(cfg):
    return BBox(bbox=cfg['bbox'], crs=CRS.WGS84)


def get_catalog(cfg, bbox):
    config = SHConfig()
    config.sh_client_id = cfg["sh_client_id"]
    config.sh_client_secret = cfg["sh_client_secret"]

    catalog = SentinelHubCatalog(config=config)
    time_interval = tuple(cfg["time_interval"])

    # --- REVERTED: Use SENTINEL2_L2A for catalog search ---
    search_iterator = catalog.search(
        DataCollection.SENTINEL2_L2A, # Back to SENTINEL2_L2A
        bbox=bbox,
        time=time_interval,
        filter=f"eo:cloud_cover < {cfg['max_cloud_coverage']}", # This filter is appropriate for Sentinel-2
        fields={"include": ["id", "properties.datetime", "geometry"], "exclude": []}
    )

    results = list(search_iterator)
    print(f"Found {len(results)} matching scenes")
    return results, config


def parse_iso8601_utc(date_str):
    if date_str.endswith('Z'):
        date_str = date_str[:-1]
    return datetime.fromisoformat(date_str)


def download_scene(scene_info, cfg, bbox, config, index):
    scene_id = scene_info["id"]
    time = scene_info["properties"]["datetime"]
    date_obj = parse_iso8601_utc(time)
    date_str = date_obj.date().isoformat()
    print(f"Downloading scene {index+1}: {scene_id} captured on {date_str}")

    size = bbox_to_dimensions(bbox, resolution=cfg["resolution"])
    time_interval = (f"{date_str}T00:00:00", f"{date_str}T23:59:59")

    # --- REVERTED: Evalscript for Sentinel-2 B04, B03, B02 bands ---
    # Outputting 3 bands (RGB) as UINT8 (0-255 scaled values).
    evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B03", "B02"], // Requesting B04 (Red), B03 (Green), B02 (Blue)
        output: {
            bands: 3,         // Output 3 bands for RGB
            sampleType: "UINT8" // Use UINT8 for 0-255 scaled visual image
        }
    };
}

function evaluatePixel(sample) {
    // Standard scaling for a visually appealing RGB image
    return [
        Math.min(1, sample.B04 * 2.5) * 255, // Red
        Math.min(1, sample.B03 * 2.5) * 255, // Green
        Math.min(1, sample.B02 * 2.5) * 255  // Blue
    ];
}
"""

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A, # Back to SENTINEL2_L2A
                time_interval=time_interval,
                # --- REMOVED: No SAR-specific other_args for S2 ---
            )
        ],
        # MimeType.tiff is correct for TIFF output
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=config
    )

    img = request.get_data()[0] # This will be a NumPy array with shape (height, width, 3) for RGB

    # --- KEPT: Skipping logic for optical imagery ---
    if np.mean(img == 0) > 0.2:
        print(f"Skipped scene {index+1}: too much black area")
        return

    folder = os.path.join(cfg["download_folder"], f"{date_str}")
    os.makedirs(folder, exist_ok=True)

    # --- KEPT: Save TIFF directly using tifffile ---
    tifffile.imwrite(os.path.join(folder, f"{date_str}.tiff"), img) # Save the NumPy array as TIFF

    request_metadata = {
        "scene_id": scene_id,
        "date": date_str,
        "request": {
            "evalscript": evalscript.strip(),
            "input": {
                "bounds": {
                    "bbox": list(bbox),
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a", # Back to type for metadata
                        "dataFilter": {
                            "timeRange": {
                                "from": time_interval[0] + "Z",
                                "to": time_interval[1] + "Z"
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": size[0],
                "height": size[1],
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/tiff"}
                }]
            }
        }
    }

    request_json_path = os.path.join(folder, "request.json")
    with open(request_json_path, "w") as f:
        json.dump(request_metadata, f, indent=4)
    print(f"Saved request metadata to: {request_json_path}")


def download_sentinel_images():
    cfg = load_config()
    bbox = get_bbox(cfg)
    scenes, config = get_catalog(cfg, bbox)

    print("Downloading one tile per scene...")
    for index, scene in enumerate(scenes):
        try:
            download_scene(scene, cfg, bbox, config, index)
        except Exception as e:
            scene_id = scene.get("id", "unknown")
            print(f"Scene {index+1} ({scene_id}) failed.")
            traceback.print_exc() # <--- CHANGE THIS LINE to print the full traceback


if __name__ == "__main__":
    download_sentinel_images()