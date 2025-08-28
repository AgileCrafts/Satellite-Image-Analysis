import numpy as np
import tifffile
import os
import json # <--- ADDED THIS IMPORT
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes

# Function to load configuration from config.json
def load_config():
    # Assumes config.json is in a 'config' subfolder relative to the script
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.json')
    with open(config_path) as f:
        return json.load(f)

# Function to calculate NDWI
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    mndwi = np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)
    return mndwi

# Function to create a binary water mask
def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

# def mask_clouds_with_scl(scl_band, water_mask):
#     cloud_classes = {3, 8, 9, 10}
#     mask = ~np.isin(scl_band, list(cloud_classes))
#     water_mask[~mask] = -2  # set cloud pixels to non-water
#     return water_mask


# Function to load Sentinel-2 TIFFs (B03 and B08)
def load_s2_bands(filepath):
    try:
        data = tifffile.imread(filepath)
        if data.ndim == 3 and data.shape[2] == 5:
            green_band = data[:, :, 0]  # B03
            red_band = data[:, :, 1]    # B04
            nir_band = data[:, :, 2]    # B08
            swir1_band = data[:, :, 3]  # B11
            scl_band = data[:, :, 4]
            return green_band, red_band, nir_band, swir1_band, scl_band
        else:
            raise ValueError(f"Expected 4 bands (B03, B04, B08, B11) in TIFF, but got shape {data.shape}")
    except Exception as e:
        print(f"Error loading TIFF file {filepath}: {e}")
        raise

# Function to perform change detection and save the change map
def perform_change_detection(pre_image_path, post_image_path, output_folder="change_maps"):
    print(f"Loading pre-image: {pre_image_path}")
    pre_green, pre_red, pre_nir, pre_swir1, pre_scl = load_s2_bands(pre_image_path) #edited
    print(f"Loading post-image: {post_image_path}")
    post_green, post_red, post_nir, post_swir1, post_scl = load_s2_bands(post_image_path) #edited
    
    
    
    #----Edited---

    print("Calculating MNDWI for pre-image...")
    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    print("Calculating MNDWI for post-image...")
    post_mndwi = calculate_mndwi(post_green, post_swir1)
    
    

    # ndwi_threshold = 0.1
    print(f"Applying MNDWI threshold: Adaptive threshold to create water masks.")
    
    # Adaptive threshold for pre-image
    

    pre_thresh = threshold_otsu(pre_mndwi)
    

    # Adaptive threshold for post-image
    post_thresh = threshold_otsu(post_mndwi)
    
    
    
    pre_mask = create_water_mask(pre_mndwi, threshold=pre_thresh) 
    post_mask = create_water_mask(post_mndwi, threshold=post_thresh) 
        
    
    pre_mask = remove_small_holes(pre_mask, area_threshold=64)
    post_mask = remove_small_holes(post_mask, area_threshold=64)
    
    pre_mask = remove_small_objects(pre_mask, min_size=20)
    post_mask = remove_small_objects(post_mask, min_size=20)
    
    
    # pre_mask = mask_clouds_with_scl(pre_scl,pre_mask )
    # post_mask = mask_clouds_with_scl(post_scl,post_mask )
    #------

    if pre_mask.shape != post_mask.shape:
        print("Warning: Pre and Post image masks have different shapes. This may lead to incorrect results.")
        min_rows = min(pre_mask.shape[0], post_mask.shape[0])
        min_cols = min(pre_mask.shape[1], post_mask.shape[1])
        pre_mask = pre_mask[:min_rows, :min_cols]
        post_mask = post_mask[:min_rows, :min_cols]

    print("Performing change detection...")
    pre_mask_int = pre_mask.astype(np.uint8)
    post_mask_int = post_mask.astype(np.uint8)

    change_map_rgb = np.zeros((pre_mask.shape[0], pre_mask.shape[1], 3), dtype=np.uint8)

    COLOR_PERSISTENT_WATER = [0, 0, 255]  # Blue
    COLOR_NEW_WATER        = [0, 255, 0]  # Green (Land to Water)
    COLOR_LOST_WATER       = [255, 0, 0]  # Red (Water to Land)
    COLOR_NO_CHANGE_LAND   = [128, 128, 128] # Gray (Land to Land) - Optional, default is black

    no_change_land_mask = (pre_mask_int == 0) & (post_mask_int == 0)
    change_map_rgb[no_change_land_mask] = COLOR_NO_CHANGE_LAND

    persistent_water_mask = (pre_mask_int == 1) & (post_mask_int == 1)
    change_map_rgb[persistent_water_mask] = COLOR_PERSISTENT_WATER

    new_water_mask = (pre_mask_int == 0) & (post_mask_int == 1)
    change_map_rgb[new_water_mask] = COLOR_NEW_WATER

    lost_water_mask = (pre_mask_int == 1) & (post_mask_int == 0)
    change_map_rgb[lost_water_mask] = COLOR_LOST_WATER

    os.makedirs(output_folder, exist_ok=True)
    
    # These base_date_str variables are used to construct the output filename
    # We can refine this to use the dates directly passed for clarity if desired,
    # but for now, it works correctly based on path parsing.
    
    
    pre_date_str_from_path = os.path.basename(os.path.dirname(pre_image_path))
    post_date_str_from_path = os.path.basename(os.path.dirname(post_image_path))
    output_filename = f"edited_water_change_map_{pre_date_str_from_path}_to_{post_date_str_from_path}.png"

    output_filepath = os.path.join(output_folder, output_filename)

    print(f"Saving change map to: {output_filepath}")

    Image.fromarray(change_map_rgb).save(output_filepath)
    print("Water change detection and map generation complete!")
    return output_filepath

# Function for creating the collage
def create_image_collage(pre_rgb_path, post_rgb_path, change_map_path, output_collage_path,
                         pre_date, post_date, change_date_range_str, label_font_path=None):
    """
    Combines three images (pre-RGB, post-RGB, change map) into a single collage
    with labels and dates, arranged side-by-side.
    """
    print(f"\nCreating image collage...")
    print(f"Loading pre-RGB: {pre_rgb_path}")
    img_pre = Image.open(pre_rgb_path)
    print(f"Loading post-RGB: {post_rgb_path}")
    img_post = Image.open(post_rgb_path)
    print(f"Loading change map: {change_map_path}")
    img_change = Image.open(change_map_path)

    if img_pre.mode != 'RGB': img_pre = img_pre.convert('RGB')
    if img_post.mode != 'RGB': img_post = img_post.convert('RGB')
    if img_change.mode != 'RGB': img_change = img_change.convert('RGB')

    width, height = img_pre.size

    label_pre = f"Pre-Image (Original) - {pre_date}"
    label_post = f"Post-Image (Original) - {post_date}"
    label_change = f"Water Changes Detected ({change_date_range_str})"

    font_size = max(20, int(height * 0.03 * 1.5))
    try:
        if label_font_path and os.path.exists(label_font_path):
            font = ImageFont.truetype(label_font_path, font_size)
        else:
            font = ImageFont.load_default()
            print("Warning: Custom font not found. Using default Pillow font. For better labels, provide a font path.")
    except Exception as e:
        print(f"Error loading font: {e}. Using default Pillow font.")
        font = ImageFont.load_default()

    _, _, text_width, text_height_approx = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0,0), "A", font=font)
    text_padding = int(font_size * 0.2)

    total_width = (width * 3) + (text_padding * 4)
    total_height = height + text_height_approx + (text_padding * 3)

    collage = Image.new('RGB', (total_width, total_height), color = (255, 255, 255))
    draw = ImageDraw.Draw(collage)

    x_offset = text_padding
    y_offset_images = text_height_approx + (text_padding * 2)

    draw.text((x_offset, text_padding), label_pre, font=font, fill=(0,0,0))
    collage.paste(img_pre, (x_offset, y_offset_images))

    x_offset += width + text_padding
    draw.text((x_offset, text_padding), label_post, font=font, fill=(0,0,0))
    collage.paste(img_post, (x_offset, y_offset_images))

    x_offset += width + text_padding
    draw.text((x_offset, text_padding), label_change, font=font, fill=(0,0,0))
    collage.paste(img_change, (x_offset, y_offset_images))

    collage.save(output_collage_path)
    print(f"Collage saved to: {output_collage_path}")


if __name__ == "__main__":
    # --- LOAD CONFIGURATION ---
    cfg = load_config()
    analysis_settings = cfg['analysis_settings']

    # Retrieve dates and paths from config
    pre_date = analysis_settings['pre_date']
    post_date = analysis_settings['post_date']
    downloads_base_path = analysis_settings['downloads_base_path']
    wadownloads_base_path = analysis_settings['wadownloads_base_path']
    

    # --- DYNAMICALLY CONSTRUCT PATHS USING CONFIG VALUES ---
    pre_image_ndwi_path = os.path.join(downloads_base_path, pre_date, f"{pre_date}.tiff")
    post_image_ndwi_path = os.path.join(downloads_base_path, post_date, f"{post_date}.tiff")

    output_wadownloads_folder = wadownloads_base_path # Now directly from config
    
    #----Edited----
    
    # --- VALIDATE INPUT FILES ---
    missing_files = []
    for file_path in [pre_image_ndwi_path]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("\nThe following required files are missing:")
        for f in missing_files:
            print(f"   - {f}")
        print("Please select another date as first date")
        exit(1)
        
        
    missing_files = []
    for file_path in [post_image_ndwi_path]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("\nThe following required files are missing:")
        for f in missing_files:
            print(f"   - {f}")
        print("Please select another date as second date")
        exit(1)
    

    print("\n--- Running Water Change Detection ---")
    generated_change_map_path = perform_change_detection(pre_image_ndwi_path, post_image_ndwi_path, output_wadownloads_folder)

    print("\n--- Running Image Collage Creation ---")
    pre_image_rgb_path = os.path.join(wadownloads_base_path, f"{pre_date}_RGB.jpg")
    post_image_rgb_path = os.path.join(wadownloads_base_path, f"{post_date}_RGB.jpg")

    
    
    # Labels are now directly from config dates
    pre_date_for_label = pre_date
    post_date_for_label = post_date
    change_date_range_for_label = f"{pre_date_for_label} to {post_date_for_label}"

    change_map_path_for_collage = generated_change_map_path

    collage_output_path = os.path.join(output_wadownloads_folder, "water_change_collage.png")

    font_file_path = None

    create_image_collage(pre_image_rgb_path, post_image_rgb_path, change_map_path_for_collage, collage_output_path,
                         pre_date_for_label, post_date_for_label, change_date_range_for_label, label_font_path=font_file_path)

    print("\nAll tasks completed. Check your 'wadownloads' folder for results.")