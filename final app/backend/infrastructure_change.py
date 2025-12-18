# builtup_analysis.py
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
import tifffile
import json
import os
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

    return numerator / denominator


def load_s2_bands_from_bytes(tiff_bytes):
    """
    Assumes order of bands: (Blue, Green, Red, NIR, SWIR1)
    """
    data = tifffile.imread(io.BytesIO(tiff_bytes))
    if data.ndim == 3 and data.shape[2] == 5:
        return data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3], data[:, :, 4]
    else:
        raise ValueError(f"Expected 5 bands in TIFF, got {data.shape}")

# ---------------- BUILT-UP CHANGE MAP ----------------
def generate_builtup_change_map(pre_bytes, post_bytes, output_dir="./output1"):
    pre_blue, pre_green, pre_red, pre_nir, pre_swir1 = load_s2_bands_from_bytes(pre_bytes)
    post_blue, post_green, post_red, post_nir, post_swir1 = load_s2_bands_from_bytes(post_bytes)

    # pre_ndbi = calculate_ndbi(pre_swir1, pre_nir)
    # post_ndbi = calculate_ndbi(post_swir1, post_nir)
    pre_baei=calculate_baei(pre_swir1, pre_red, pre_green)
    post_baei=calculate_baei(post_swir1, post_red, post_green)

    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    post_mndwi = calculate_mndwi(post_green, post_swir1)
    pre_mndwi_thresh = threshold_otsu(pre_mndwi)
    post_mndwi_thresh = threshold_otsu(post_mndwi)
    
    pre_water_mask = create_water_mask(pre_mndwi,pre_mndwi_thresh)
    post_water_mask=create_water_mask(post_mndwi,post_mndwi_thresh)


    # pre_thresh = adaptive_ndbi_threshold(pre_ebbi, percentile=85)
    # post_thresh = adaptive_ndbi_threshold(post_ebbi, percentile=85)
    pre_thresh = threshold_otsu(pre_baei)
    post_thresh = threshold_otsu(post_baei)
    
    pre_ndvi = calculate_ndvi(pre_nir, pre_red)
    post_ndvi = calculate_ndvi(post_nir, post_red)


    pre_mask = create_builtup_mask(pre_baei, pre_thresh)
    post_mask = create_builtup_mask(post_baei, post_thresh)

    # Remove water
    pre_mask[pre_water_mask] = False
    post_mask[post_water_mask] = False
    
    veg_threshold = 0.2
    pre_mask[pre_ndvi > veg_threshold] = False
    post_mask[post_ndvi > veg_threshold] = False

    # Clean masks
    # pre_mask = remove_small_objects(remove_small_holes(pre_mask, area_threshold=64), min_size=20)
    # post_mask = remove_small_objects(remove_small_holes(post_mask, area_threshold=64), min_size=20)

    # Ensure same shape
    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])
    pre_mask = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    COLOR_PERSISTENT_BUILTUP = [200, 0, 200]  # purple
    COLOR_NEW_BUILTUP = [255, 165, 0]        # orange
    COLOR_LOST_BUILTUP = [0, 255, 255]       # cyan
    COLOR_NO_CHANGE_OTHER = [128, 128, 128]  # grey

    pre_int = pre_mask.astype(np.uint8)
    post_int = post_mask.astype(np.uint8)

    change_map_rgb[(pre_int==0) & (post_int==0)] = COLOR_NO_CHANGE_OTHER
    change_map_rgb[(pre_int==1) & (post_int==1)] = COLOR_PERSISTENT_BUILTUP
    change_map_rgb[(pre_int==0) & (post_int==1)] = COLOR_NEW_BUILTUP
    change_map_rgb[(pre_int==1) & (post_int==0)] = COLOR_LOST_BUILTUP
    
    # Assign colors and count pixels
    persistent_count = np.sum((pre_int == 1) & (post_int == 1))
    new_count = np.sum((pre_int == 0) & (post_int == 1))
    lost_count = np.sum((pre_int == 1) & (post_int == 0))
    no_change_count = np.sum((pre_int == 0) & (post_int == 0))
    
    
    # Calculate total area (assuming 10m x 10m resolution per pixel)
    total_pixels = min_rows * min_cols
    pixel_area_m2 = 100  # 10m x 10m
    persistent_area_m2 = (persistent_count / total_pixels) * (min_rows * min_cols * pixel_area_m2)
    new_area_m2 = (new_count / total_pixels) * (min_rows * min_cols * pixel_area_m2)
    lost_area_m2 = (lost_count / total_pixels) * (min_rows * min_cols * pixel_area_m2)
    no_change_area_m2 = (no_change_count / total_pixels) * (min_rows * min_cols * pixel_area_m2)
    
    print(new_area_m2)

    # Convert to hectares (1 hectare = 10,000 m²)
    persistent_area_ha = persistent_area_m2 / 10000
    new_area_ha = new_area_m2 / 10000
    lost_area_ha = lost_area_m2 / 10000
    no_change_area_ha = no_change_area_m2 / 10000

    # Store statistics
    area_stats = {
        "Persistent Built-up": {"area_ha": persistent_area_ha, "color": COLOR_PERSISTENT_BUILTUP},
        "New Built-up": {"area_ha": new_area_ha, "color": COLOR_NEW_BUILTUP},
        "Lost Built-up": {"area_ha": lost_area_ha, "color": COLOR_LOST_BUILTUP},
        "Non-Built-up": {"area_ha": no_change_area_ha, "color": COLOR_NO_CHANGE_OTHER}
    }
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the change map image
    change_map_filename = "change_map.png"
    change_map_path = os.path.join(output_dir, change_map_filename)
    Image.fromarray(change_map_rgb).save(change_map_path)

    buf = io.BytesIO()
    Image.fromarray(change_map_rgb).save(buf, format="PNG")
    buf.seek(0)
    return buf.read(), area_stats

if __name__ == "__main__":
    pre_path = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\pre_image.tif"
    post_path = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\post_image.tif"
    with open(pre_path, "rb") as f:
        pre_bytes = f.read()
    with open(post_path, "rb") as f:
        post_bytes = f.read()
        
        
    generate_builtup_change_map(pre_bytes, post_bytes)