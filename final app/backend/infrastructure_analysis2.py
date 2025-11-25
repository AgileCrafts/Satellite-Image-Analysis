# builtup_analysis.py
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
import tifffile
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Image as ImageModel, ChangeMap  
import json
import rasterio
from rasterio.transform import from_origin



def extract_purple_mask(change_map_bytes):
    """
    Extract purple-only mask from full infrastructure change map.
    Purple = built-up increase (R + B high, G low).
    """
    img = Image.open(io.BytesIO(change_map_bytes)).convert("RGB")
    arr = np.array(img)

    # Detect PURPLE: high red & blue, low green
    mask = (
        (arr[:, :, 0] > 150) &     # Red high
        (arr[:, :, 2] > 150) &     # Blue high
        (arr[:, :, 1] < 80)        # Green low
    )

    purple_mask = np.zeros_like(arr)
    purple_mask[mask] = [160, 32, 240]  # Actual purple (RGB)

    buf = io.BytesIO()
    Image.fromarray(purple_mask).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

def save_purple_mask_tif(change_map_bytes, output_tif="purple_mask.tif", pixel_size=10, reference_tif=None):
    """
    Convert purple mask to binary GeoTIFF.
    255 = purple (built-up change), 0 = background.
    """
    img = Image.open(io.BytesIO(change_map_bytes)).convert("RGB")
    arr = np.array(img)

    # Purple = high red, high blue, low green
    binary_mask = (
        (arr[:, :, 0] > 150) & 
        (arr[:, :, 2] > 150) & 
        (arr[:, :, 1] < 80)
    ).astype(np.uint8) * 255

    if reference_tif:
        with rasterio.open(reference_tif) as src:
            profile = src.profile
        profile.update(count=1, dtype='uint8')
    else:
        transform = from_origin(0, 0, pixel_size, pixel_size)
        profile = {
            'driver': 'GTiff',
            'height': binary_mask.shape[0],
            'width': binary_mask.shape[1],
            'count': 1,
            'dtype': 'uint8',
            'transform': transform,
            'crs': "+proj=utm +zone=46 +datum=WGS84"
        }

    with rasterio.open(output_tif, 'w', **profile) as dst:
        dst.write(binary_mask, 1)

    print(f"Purple mask TIF saved: {output_tif}")
    return binary_mask

def overlay_purple_mask_on_rgb(rgb_bytes, mask_bytes, alpha=0.6):
    """
    Overlay purple mask on RGB Sentinel-2 image.
    Purple = R & B high, G low.
    """
    rgb_img = Image.open(io.BytesIO(rgb_bytes)).convert("RGB")
    mask_img = Image.open(io.BytesIO(mask_bytes)).convert("RGB")

    mask_img = mask_img.resize(rgb_img.size, resample=Image.NEAREST)

    rgb_arr = np.array(rgb_img, dtype=np.uint8)
    mask_arr = np.array(mask_img, dtype=np.uint8)

    # Detect purple
    purple_mask = (
        (mask_arr[:, :, 0] > 150) &
        (mask_arr[:, :, 2] > 150) &
        (mask_arr[:, :, 1] < 80)
    )

    overlay = rgb_arr.copy()

    # For purple color blending
    overlay[purple_mask, 0] = (160 * alpha + overlay[purple_mask, 0] * (1 - alpha)).astype(np.uint8)
    overlay[purple_mask, 1] = (32 * alpha + overlay[purple_mask, 1] * (1 - alpha)).astype(np.uint8)
    overlay[purple_mask, 2] = (240 * alpha + overlay[purple_mask, 2] * (1 - alpha)).astype(np.uint8)

    overlay_img = Image.fromarray(overlay)
    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ---------------- NDBI & MASK ----------------
def calculate_ndbi(swir1_band, nir_band):
    denominator = swir1_band + nir_band
    return np.where(denominator == 0, 0, (swir1_band - nir_band) / denominator)

def create_builtup_mask(ndbi_image, threshold):
    return ndbi_image > threshold

def adaptive_ndbi_threshold(ndbi, percentile=85):
    return np.percentile(ndbi, percentile)

def calculate_nbi(swir1_band, red_band, nir_band):
        """New Built-up Index dramatically better than NDBI in wet/tropical areas"""
        numerator = swir1_band * red_band
        denominator = nir_band
        return np.where(denominator == 0, 0, numerator / denominator)

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

def calculate_ndisi(swir1_band, red_band):
        denominator = swir1_band + red_band
        return np.where(denominator == 0, 0, (swir1_band - red_band) / denominator)


def load_s2_bands_from_bytes(tiff_bytes):
    """
    Assumes order of bands: (Green, Red, NIR, SWIR1, SCL)
    """
    data = tifffile.imread(io.BytesIO(tiff_bytes))
    if data.ndim == 3 and data.shape[2] == 5:
        return data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3], data[:, :, 4]
    else:
        raise ValueError(f"Expected 5 bands in TIFF, got {data.shape}")

# ---------------- BUILT-UP CHANGE MAP ----------------
def generate_builtup_change_map(pre_bytes, post_bytes):
    pre_green, pre_red, pre_nir, pre_swir1, _ = load_s2_bands_from_bytes(pre_bytes)
    post_green, post_red, post_nir, post_swir1, _ = load_s2_bands_from_bytes(post_bytes)
    
    #----------------- Using ndbi --------------------------

    pre_ndbi = calculate_ndbi(pre_swir1, pre_nir)
    post_ndbi = calculate_ndbi(post_swir1, post_nir)


    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    post_mndwi = calculate_mndwi(post_green, post_swir1)
    pre_mndwi_thresh = threshold_otsu(pre_mndwi)
    post_mndwi_thresh = threshold_otsu(post_mndwi)
    
    pre_water_mask = create_water_mask(pre_mndwi,pre_mndwi_thresh)
    post_water_mask=create_water_mask(post_mndwi,post_mndwi_thresh)


    # pre_thresh = adaptive_ndbi_threshold(pre_ndbi, percentile=85)
    # post_thresh = adaptive_ndbi_threshold(post_ndbi, percentile=85)
    # pre_thresh = threshold_otsu(pre_ndbi)
    # post_thresh = threshold_otsu(post_ndbi)
    
    # combined = np.concatenate([pre_ndbi.flatten(), post_ndbi.flatten()])
    # global_thresh = threshold_otsu(combined)
    # pre_thresh=global_thresh
    # post_thresh=global_thresh
    
    pre_ndvi = calculate_ndvi(pre_nir,pre_red )
    post_ndvi = calculate_ndvi(post_nir, post_red)


    # pre_mask = create_builtup_mask(pre_ndbi, pre_thresh)
    # post_mask = create_builtup_mask(post_ndbi, post_thresh)

    # # Remove water
    # pre_mask[pre_water_mask] = False
    # post_mask[post_water_mask] = False
    
    # veg_threshold = 0.05
    # pre_mask[pre_ndvi > veg_threshold] = False
    # post_mask[post_ndvi > veg_threshold] = False
    

    #*******************Using NBI *********************

    
    # Then in generate_builtup_change_map():
    pre_nbi = calculate_nbi(pre_swir1, pre_red, pre_nir)
    post_nbi = calculate_nbi(post_swir1, post_red, post_nir)
    
    pre_thresh = np.percentile(pre_nbi, 85)
    post_thresh = np.percentile(post_nbi, 85)

    # Use nbi instead of ndbi everywhere
    delta_index = post_nbi - pre_nbi
    strong_nbi_change = delta_index > 0.15   # typical threshold for NBI
    
    pre_mask_raw = pre_nbi > pre_thresh
    post_mask_raw = post_nbi > post_thresh

    enhanced_new_built = (post_mask_raw & strong_nbi_change) 

    # Apply water removal
    pre_mask = pre_mask_raw.copy()
    post_mask = enhanced_new_built.copy()
    pre_mask[pre_water_mask] = False
    post_mask[post_water_mask] = False

    
    veg_threshold = 0.25
    pre_mask[pre_nbi > veg_threshold] = False
    post_mask[post_nbi > veg_threshold] = False

    #-------------- After adding ndisi ---------------

    # pre_ndisi = calculate_ndisi(pre_swir1, pre_red)
    # post_ndisi = calculate_ndisi(post_swir1, post_red)

    # # Δ change detection
    # delta_ndbi = post_ndbi - pre_ndbi
    # delta_ndisi = post_ndisi - pre_ndisi

    # # Initial masks (based on NDBI)
    # pre_mask_raw = pre_ndbi > pre_thresh
    # post_mask_raw = post_ndbi > post_thresh

    # # Strong NDBI increase = new construction
    # strong_ndbi_change = delta_ndbi > 0.05

    # # NDISI high = built-up (captures concrete, construction sites)
    # # ndiri_like_built = post_ndisi > 0.05
    
    # # strong_ndisi_change = delta_ndisi > 0.03


    # # Combine signals
    # enhanced_new_built = (post_mask_raw & strong_ndbi_change) 

    # # Apply water removal
    # pre_mask = pre_mask_raw.copy()
    # post_mask = enhanced_new_built.copy()
    # pre_mask[pre_water_mask] = False
    # post_mask[post_water_mask] = False

    
    # veg_threshold = 0.4
    # pre_mask[pre_ndvi > veg_threshold] = False
    # post_mask[post_ndvi > veg_threshold] = False
    
    #--------------------------------------------------------


    # Clean masks
    # pre_mask = remove_small_objects(remove_small_holes(pre_mask, area_threshold=300), min_size=150)
    # post_mask = remove_small_objects(remove_small_holes(post_mask, area_threshold=300), min_size=150)

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

    buf = io.BytesIO()
    Image.fromarray(change_map_rgb).save(buf, format="PNG")
    buf.seek(0)
    return buf.read(), area_stats

# ---------------- COLLAGE ----------------
def create_image_collage(pre_rgb_bytes, post_rgb_bytes, change_map_bytes, pre_date, post_date, label_font_path=None):
    img_pre = Image.open(io.BytesIO(pre_rgb_bytes)).convert("RGB")
    img_post = Image.open(io.BytesIO(post_rgb_bytes)).convert("RGB")
    img_change = Image.open(io.BytesIO(change_map_bytes)).convert("RGB")

    width, height = img_pre.size
    font_size = max(20, int(height * 0.03 * 1.5))
    try:
        if label_font_path:
            font = ImageFont.truetype(label_font_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    _, _, _, text_height = ImageDraw.Draw(Image.new("RGB", (1,1))).textbbox((0,0), "A", font=font)
    padding = int(font_size * 0.2)
    total_width = width*3 + padding*4
    total_height = height + text_height + padding*3
    collage = Image.new("RGB", (total_width, total_height), (255,255,255))
    draw = ImageDraw.Draw(collage)

    x_offset = padding
    y_offset = text_height + padding*2
    draw.text((x_offset, padding), f"Pre-RGB: {pre_date}", font=font, fill=(0,0,0))
    collage.paste(img_pre, (x_offset, y_offset))

    x_offset += width + padding
    draw.text((x_offset, padding), f"Post-RGB: {post_date}", font=font, fill=(0,0,0))
    collage.paste(img_post, (x_offset, y_offset))

    x_offset += width + padding
    draw.text((x_offset, padding), "Built-up Change Map", font=font, fill=(0,0,0))
    collage.paste(img_change, (x_offset, y_offset))

    buf = io.BytesIO()
    collage.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

# ---------------- MAIN DB FUNCTION ----------------
def run_builtup_analysis(change_map_id: int):
    db: Session = SessionLocal()
    try:
        cm = db.query(ChangeMap).filter(ChangeMap.id==change_map_id).first()
        if not cm:
            print(f"ChangeMap id={change_map_id} not found")
            return

        # Fetch pre/post images from DB
        pre_img = db.query(ImageModel).filter(ImageModel.id==cm.pre_image_id).first()
        post_img = db.query(ImageModel).filter(ImageModel.id==cm.post_image_id).first()
        if not pre_img or not post_img:
            print("Pre or post image not found in DB")
            return

        # Generate built-up change map
        builtup_bytes, area_stats = generate_builtup_change_map(pre_img.ndwi_data, post_img.ndwi_data)
        cm.builtup_analysis_image = builtup_bytes

        # Generate collage using RGB images from DB
        collage_bytes = create_image_collage(pre_img.rgb_data, post_img.rgb_data, builtup_bytes,
                                             str(cm.from_date), str(cm.to_date))
        cm.builtup_collage_image = collage_bytes
        cm.builtup_area_stats = area_stats


         # Extract purple-only overlay mask
        purple_mask_bytes = extract_purple_mask(builtup_bytes)
        
        # Overlay red mask on post-RGB image
        overlay_bytes = overlay_purple_mask_on_rgb(post_img.rgb_data,builtup_bytes , alpha=0.6)
        cm.builtup_overlay = overlay_bytes
        
        binary_mask = save_purple_mask_tif(purple_mask_bytes, "new_builtup_mask.tif")


        # Save overlay to file
        overlay_img = Image.open(io.BytesIO(overlay_bytes))
        overlay_img.save("builtup_overlay.png")
        print("Overlay saved as builtup_overlay.png")
        
        
        db.commit()
        print(f"Built-up analysis completed for ChangeMap ID {change_map_id}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# ---------------- CLI ----------------
if __name__ == "__main__":
    change_map_id = int(input("Enter ChangeMap ID to perform water analysis: "))
    run_builtup_analysis(change_map_id)