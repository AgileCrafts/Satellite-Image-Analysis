import os
import json
from sentinelhub import (
    SHConfig, BBox, CRS, DataCollection,
    SentinelHubRequest, MimeType, bbox_to_dimensions
)
from PIL import Image
from datetime import datetime

# Function to load configuration from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.json')
    with open(config_path) as f:
        return json.load(f)

def get_bbox(cfg):
    return BBox(bbox=cfg['bbox'], crs=CRS.WGS84)

def parse_iso8601_utc(date_str):
    if date_str.endswith('Z'):
        date_str = date_str[:-1]
    return datetime.fromisoformat(date_str)

# --- MODIFIED FUNCTION SIGNATURE AND VARIABLE USAGE ---
def download_rgb_scene(json_config, date_to_download, sh_config_obj):
    """
    Downloads an RGB image for a given date.
    json_config: The dictionary loaded from config.json.
    date_to_download: The date string for the image.
    sh_config_obj: The SentinelHub SHConfig object for authentication.
    """
    bbox = get_bbox(json_config) # Use json_config for bbox
    size = bbox_to_dimensions(bbox, resolution=json_config["resolution"]) # Use json_config for resolution
    time_interval = (f"{date_to_download}T00:00:00", f"{date_to_download}T23:59:59")

    print(f"Attempting to download RGB image for {date_to_download}")

    evalscript_rgb = """
    //VERSION=3
    function setup() {
        return {
            input: ["B04", "B03", "B02"],
            output: {
                bands: 3,
                sampleType: "UINT8"
            }
        };
    }

    function evaluatePixel(sample) {
        return [
            Math.min(1, sample.B04 * 2.5) * 255,
            Math.min(1, sample.B03 * 2.5) * 255,
            Math.min(1, sample.B02 * 2.5) * 255
        ];
    }
    """

    request = SentinelHubRequest(
        evalscript=evalscript_rgb,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=sh_config_obj # <-- Use sh_config_obj here for SentinelHubRequest
    )

    try:
        img_data = request.get_data()
        if not img_data:
            print(f"No data returned for {date_to_download}. Skipping.")
            return

        img = img_data[0]

        # --- CORRECTED LINE: Use json_config to get the output path ---
        rgb_output_folder = json_config['analysis_settings']['wadownloads_base_path']
        os.makedirs(rgb_output_folder, exist_ok=True)

        rgb_filepath = os.path.join(rgb_output_folder, f"{date_to_download}_RGB.jpg")
        
        Image.fromarray(img).save(rgb_filepath)
        print(f"Successfully downloaded and saved RGB image to: {rgb_filepath}")

    except Exception as e:
        import traceback
        print(f"Failed to download RGB image for {date_to_download}: {e}")
        traceback.print_exc()


def download_rgb_images():
    cfg = load_config() # This is the loaded JSON config dictionary
    sh_config = SHConfig() # This is the SHConfig object
    sh_config.sh_client_id = cfg["sh_client_id"]
    sh_config.sh_client_secret = cfg["sh_client_secret"]

    pre_date = cfg['analysis_settings']['pre_date']
    post_date = cfg['analysis_settings']['post_date']
    dates_for_rgb = [pre_date, post_date]
    
    #----Edited----
    
    # --- VALIDATE INPUT FILES ---
    downloads_base_path = cfg['analysis_settings']['downloads_base_path']
    pre_image_ndwi_path = os.path.join(downloads_base_path, pre_date, f"{pre_date}.tiff")
    post_image_ndwi_path = os.path.join(downloads_base_path, post_date, f"{post_date}.tiff")

    missing_files = []
    for file_path in [pre_image_ndwi_path]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("Please select another date as first date")
        exit(1)
        
        
    missing_files = []
    for file_path in [post_image_ndwi_path]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("Please select another date as second date")
        exit(1)

    for date_str in dates_for_rgb:
        # --- CORRECTED CALL: Pass the loaded JSON config (cfg) and the SHConfig object (sh_config) ---
        download_rgb_scene(cfg, date_str, sh_config)

if __name__ == "__main__":
    download_rgb_images()