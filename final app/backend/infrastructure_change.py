# builtup_analysis.py

import io
import numpy as np
from PIL import Image
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
import json
import os

# 🔹 Added (for GeoJSON)
import rasterio
from rasterio import features
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
import pyproj

# ---------------- NDBI & MASK ----------------
def calculate_ndbi(swir1_band, nir_band):
    denominator = swir1_band + nir_band
    return np.where(denominator == 0, 0, (swir1_band - nir_band) / denominator)

def create_builtup_mask(ndbi_image, threshold):
    return ndbi_image > threshold

def adaptive_ndbi_threshold(ndbi, percentile=85):
    return np.percentile(ndbi, percentile)

#---------------- MNDWI & MASK ----------------
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    return np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)

def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

#---------------- NDVI & MASK ----------------
def calculate_ndvi(nir_band, red_band):
    denominator = nir_band + red_band
    return np.where(denominator == 0, 0, (nir_band - red_band) / denominator)

def calculate_baei(swir1_band, red_band, green_band):
    numerator = (red_band + 0.3)
    denominator = (swir1_band + green_band)
    return numerator / (denominator + 1e-6)

# ---------------- LOAD (WITH GEOREF, NAME UNCHANGED) ----------------
def load_s2_bands_from_bytes(tiff_bytes):
    with rasterio.open(io.BytesIO(tiff_bytes)) as src:
        data = src.read()
        transform = src.transform
        crs = src.crs

    if data.shape[0] != 5:
        raise ValueError("Expected 5-band Sentinel-2 image")

    return (
        data[0], data[1], data[2], data[3], data[4],
        transform, crs
    )

# ---------------- BUILT-UP CHANGE MAP ----------------
def generate_builtup_change_map(pre_bytes, post_bytes, output_dir="./output1"):

    pre_blue, pre_green, pre_red, pre_nir, pre_swir1, transform, crs = load_s2_bands_from_bytes(pre_bytes)
    post_blue, post_green, post_red, post_nir, post_swir1, _, _ = load_s2_bands_from_bytes(post_bytes)

    pre_baei = calculate_baei(pre_swir1, pre_red, pre_green)
    post_baei = calculate_baei(post_swir1, post_red, post_green)

    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    post_mndwi = calculate_mndwi(post_green, post_swir1)

    pre_mndwi_thresh = threshold_otsu(pre_mndwi)
    post_mndwi_thresh = threshold_otsu(post_mndwi)

    pre_water_mask = create_water_mask(pre_mndwi, pre_mndwi_thresh)
    post_water_mask = create_water_mask(post_mndwi, post_mndwi_thresh)

    pre_thresh = threshold_otsu(pre_baei)
    post_thresh = threshold_otsu(post_baei)

    pre_ndvi = calculate_ndvi(pre_nir, pre_red)
    post_ndvi = calculate_ndvi(post_nir, post_red)

    pre_mask = create_builtup_mask(pre_baei, pre_thresh)
    post_mask = create_builtup_mask(post_baei, post_thresh)

    # Remove water & vegetation
    pre_mask[pre_water_mask] = False
    post_mask[post_water_mask] = False

    veg_threshold = 0.2
    pre_mask[pre_ndvi > veg_threshold] = False
    post_mask[post_ndvi > veg_threshold] = False

    # Ensure same shape
    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])

    pre_mask = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    # ---------------- CHANGE MAP (UNCHANGED) ----------------
    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)

    COLOR_PERSISTENT_BUILTUP = [200, 0, 200]
    COLOR_NEW_BUILTUP = [255, 165, 0]     # 🟧 ORANGE
    COLOR_LOST_BUILTUP = [0, 255, 255]
    COLOR_NO_CHANGE_OTHER = [128, 128, 128]

    pre_int = pre_mask.astype(np.uint8)
    post_int = post_mask.astype(np.uint8)

    change_map_rgb[(pre_int==0) & (post_int==0)] = COLOR_NO_CHANGE_OTHER
    change_map_rgb[(pre_int==1) & (post_int==1)] = COLOR_PERSISTENT_BUILTUP
    change_map_rgb[(pre_int==0) & (post_int==1)] = COLOR_NEW_BUILTUP
    change_map_rgb[(pre_int==1) & (post_int==0)] = COLOR_LOST_BUILTUP

    os.makedirs(output_dir, exist_ok=True)
    Image.fromarray(change_map_rgb).save(os.path.join(output_dir, "change_map.png"))

    # =====================================================
    # 🔥 EXTRACT ONLY ORANGE (NEW BUILT-UP) → GEOJSON
    # =====================================================
    new_builtup_mask = (pre_int == 0) & (post_int == 1)

    new_builtup_mask = remove_small_objects(
        remove_small_holes(new_builtup_mask, 100),
        min_size=300
    )

    polygons = []
    for geom, val in features.shapes(
        new_builtup_mask.astype(np.uint8),
        transform=transform
    ):
        if val == 1:
            poly = shape(geom)
            if poly.is_valid and not poly.is_empty:
                polygons.append(poly)

    if polygons:
        merged = unary_union(polygons).simplify(0.00005, preserve_topology=True)
    else:
        merged = None

    if merged and crs and str(crs) != "EPSG:4326":
        transformer = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        merged = transform(transformer.transform, merged)

    if merged and not merged.is_empty:
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": mapping(merged),
                "properties": {
                    "change": "new_builtup",
                    "color": "orange"
                }
            }]
        }
    else:
        geojson = {"type": "FeatureCollection", "features": []}

    geojson_path = os.path.join(output_dir, "new_builtup.geojson")
    with open(geojson_path, "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"GeoJSON saved: {geojson_path}")

    return{
        "geojson": geojson
    }

# ---------------- MAIN (UNCHANGED STYLE) ----------------
if __name__ == "__main__":
    pre_path = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\pre_image.tif"
    post_path = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\post_image.tif"

    with open(pre_path, "rb") as f:
        pre_bytes = f.read()
    with open(post_path, "rb") as f:
        post_bytes = f.read()

    generate_builtup_change_map(pre_bytes, post_bytes)
