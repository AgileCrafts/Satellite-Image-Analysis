import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
import tifffile
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Image as ImageModel, ChangeMap  
from datetime import datetime
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score


def extract_red_mask(change_map_bytes):
    """
    Extract red-only mask from full change map (lost water areas).
    """
    img = Image.open(io.BytesIO(change_map_bytes)).convert("RGB")
    arr = np.array(img)

    # Keep only red pixels, set all else to black
    red_mask = np.zeros_like(arr)
    mask = (arr[:, :, 0] > 150) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 80)
    red_mask[mask] = [255, 0, 0]

    buf = io.BytesIO()
    Image.fromarray(red_mask).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def overlay_mask_on_rgb(rgb_bytes, mask_bytes, alpha=0.6):
    """
    Overlay red mask on RGB Sentinel-2 image.
    """
    import numpy as np
    from PIL import Image
    import io

    rgb_img = Image.open(io.BytesIO(rgb_bytes)).convert("RGB")
    mask_img = Image.open(io.BytesIO(mask_bytes)).convert("RGB")

    # Resize mask to match RGB image
    mask_img = mask_img.resize(rgb_img.size, resample=Image.NEAREST)

    # Convert to numpy
    rgb_arr = np.array(rgb_img, dtype=np.uint8)
    mask_arr = np.array(mask_img, dtype=np.uint8)

    # Detect red pixels in mask
    red_mask = (mask_arr[:, :, 0] > 150) & (mask_arr[:, :, 1] < 80) & (mask_arr[:, :, 2] < 80)

    # Copy RGB and blend only where mask is True
    overlay = rgb_arr.copy()
    overlay[red_mask, 0] = (255 * alpha + overlay[red_mask, 0] * (1 - alpha)).astype(np.uint8)
    overlay[red_mask, 1] = (overlay[red_mask, 1] * (1 - alpha)).astype(np.uint8)
    overlay[red_mask, 2] = (overlay[red_mask, 2] * (1 - alpha)).astype(np.uint8)

    overlay_img = Image.fromarray(overlay)
    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ---------------- MNDWI & MASK ----------------
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    return np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)

def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

def load_s2_bands_from_bytes(tiff_bytes):
    data = tifffile.imread(io.BytesIO(tiff_bytes))
    if data.ndim == 3 and data.shape[2] == 5:
        return data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3], data[:, :, 4]
    else:
        raise ValueError(f"Expected 5 bands in TIFF, got {data.shape}")

# ---------------- WATER CHANGE MAP ----------------
def generate_water_change_map(pre_bytes, post_bytes):
    pre_green, _, _, pre_swir1, _ = load_s2_bands_from_bytes(pre_bytes)
    post_green, _, _, post_swir1, _ = load_s2_bands_from_bytes(post_bytes)

    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    post_mndwi = calculate_mndwi(post_green, post_swir1)

    pre_thresh = threshold_otsu(pre_mndwi)
    post_thresh = threshold_otsu(post_mndwi)

    pre_mask = remove_small_objects(remove_small_holes(create_water_mask(pre_mndwi, pre_thresh), area_threshold=400), min_size=200)
    post_mask = remove_small_objects(remove_small_holes(create_water_mask(post_mndwi, post_thresh), area_threshold=400), min_size=200)

    # Ensure same shape
    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])
    pre_mask = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    COLOR_PERSISTENT_WATER = [0, 0, 255]
    COLOR_NEW_WATER = [0, 255, 0]
    COLOR_LOST_WATER = [255, 0, 0]
    COLOR_NO_CHANGE_LAND = [128, 128, 128]

    pre_int = pre_mask.astype(np.uint8)
    post_int = post_mask.astype(np.uint8)

    change_map_rgb[(pre_int==0) & (post_int==0)] = COLOR_NO_CHANGE_LAND
    change_map_rgb[(pre_int==1) & (post_int==1)] = COLOR_PERSISTENT_WATER
    change_map_rgb[(pre_int==0) & (post_int==1)] = COLOR_NEW_WATER
    change_map_rgb[(pre_int==1) & (post_int==0)] = COLOR_LOST_WATER


    # Calculate pixel counts for each category
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

    # Store water area statistics
    water_area_stats = {
        "Persistent Water": {"area_ha": persistent_area_ha, "color": COLOR_PERSISTENT_WATER},
        "New Water": {"area_ha": new_area_ha, "color": COLOR_NEW_WATER},
        "Lost Water": {"area_ha": lost_area_ha, "color": COLOR_LOST_WATER},
        "No Change Land": {"area_ha": no_change_area_ha, "color": COLOR_NO_CHANGE_LAND}
    }
    
    buf = io.BytesIO()
    Image.fromarray(change_map_rgb).save(buf, format="PNG")
    buf.seek(0)
    return buf.read(),water_area_stats

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
    draw.text((x_offset, padding), "Water Change Map", font=font, fill=(0,0,0))
    collage.paste(img_change, (x_offset, y_offset))

    buf = io.BytesIO()
    collage.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

def extract_red_mask_as_array(change_map_bytes):
    """
    Extract red mask as binary NumPy array for pixel counting.
    """
    img = Image.open(io.BytesIO(change_map_bytes)).convert("RGB")
    arr = np.array(img)
    mask = (arr[:, :, 0] > 150) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 80)
    return mask.astype(int)  # 1 = red (lost water), 0 = else

def compute_area_based_accuracy(script_red_pixels, screenshot_red_area_sqkm, pixel_resolution_m=10):
    """
    Compute area-based accuracy metrics (0–100%) using screenshot area as reference.
    Includes IoU, coverage, and area match percentages.
    """
    if screenshot_red_area_sqkm <= 0:
        return {'error': 'Screenshot red area must be > 0'}

    # Convert predicted pixel count to area (sq km)
    script_red_area_sqkm = script_red_pixels * (pixel_resolution_m ** 2) / 1e6

    # Basic area difference and ratio
    area_diff_sqkm = abs(script_red_area_sqkm - screenshot_red_area_sqkm)
    area_ratio = script_red_area_sqkm / screenshot_red_area_sqkm if screenshot_red_area_sqkm > 0 else 0

    # Area match (% similarity in size — smoothed)
    area_match_pct = max(0, min(100, 100 * (1 - abs(1 - area_ratio) ** 0.8)))

    # Relative error (difference as % of expected)
    relative_error_pct = min(100, (area_diff_sqkm / screenshot_red_area_sqkm) * 100)

    # IoU (Intersection over Union) — for spatial overlap efficiency
    intersection = min(script_red_area_sqkm, screenshot_red_area_sqkm)
    union = script_red_area_sqkm + screenshot_red_area_sqkm - intersection
    iou_accuracy_pct = (intersection / union) * 100 if union > 0 else 0

    # Coverage accuracy — did we cover the expected area?
    coverage_pct = (intersection / screenshot_red_area_sqkm) * 100 if screenshot_red_area_sqkm > 0 else 0

    # Optional: Weighted accuracy (tunable blend of IoU + size match)
    weighted_accuracy_pct = round((iou_accuracy_pct * 0.6 + area_match_pct * 0.4), 2)

    return {
        'script_red_area_sqkm': round(script_red_area_sqkm, 4),
        'screenshot_red_area_sqkm': round(screenshot_red_area_sqkm, 4),
        'area_diff_sqkm': round(area_diff_sqkm, 4),
        'area_ratio': round(area_ratio, 3),
        'relative_error_pct': round(relative_error_pct, 2),
        'area_match_pct': round(area_match_pct, 2),       # size similarity
        'coverage_pct': round(coverage_pct, 2),           # did we cover expected area?
        'iou_accuracy_pct': round(iou_accuracy_pct, 2),   # spatial overlap efficiency
        # 'weighted_accuracy_pct': weighted_accuracy_pct    # balanced score
    }



def save_accuracy_to_txt(change_map_id, pre_date, post_date, metrics_dict, output_dir="./"):
    """
    Save accuracy metrics to a timestamped TXT file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{output_dir}accuracy_results_{timestamp}_{change_map_id}.txt"
    
    with open(filename, 'w') as f:
        f.write("Water Analysis Accuracy Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"ChangeMap ID: {change_map_id}\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Date Range: {pre_date} to {post_date}\n\n")
        
        f.write("Script Red Area (sq km):\n")
        f.write(f"- {metrics_dict['script_red_area_sqkm']}\n\n")
        
        f.write("Known Red Area from GEE Screenshot (sq km):\n")
        f.write(f"- {metrics_dict['screenshot_red_area_sqkm']}\n\n")
        
        f.write("Area-Based Accuracy:\n")
        for key, value in metrics_dict.items():
            if key not in ['script_red_area_sqkm', 'screenshot_red_area_sqkm']:
                f.write(f"- {key}: {value}\n")
    
    print(f"Accuracy report saved to: {filename}")
    return filename

# ---------------- MAIN DB FUNCTION ----------------
def run_water_analysis(change_map_id: int, red_area_from_screenshot_sqkm: float = None):
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

        # Generate water change map
        water_bytes, water_area_stats = generate_water_change_map(pre_img.ndwi_data, post_img.ndwi_data)
        cm.water_analysis_image = water_bytes
        cm.water_area_stats= water_area_stats
        
        # Extract red-only overlay mask
        red_mask_bytes = extract_red_mask(water_bytes)
        # Overlay red mask on post-RGB image
        overlay_bytes = overlay_mask_on_rgb(post_img.rgb_data, water_bytes, alpha=0.6)
        cm.encroachment_overlay = overlay_bytes

        # Save overlay to file
        overlay_img = Image.open(io.BytesIO(overlay_bytes))
        overlay_img.save("encroachment_overlay.png")
        print("Overlay saved as encroachment_overlay.png")
        
        # Generate collage
        collage_bytes = create_image_collage(pre_img.rgb_data, post_img.rgb_data, water_bytes,
                                            str(cm.from_date), str(cm.to_date))
        cm.collage_image = collage_bytes
        

        red_area_from_screenshot_sqkm = 0.035
        # Compute and save accuracy if red area provided
        if red_area_from_screenshot_sqkm is not None:
            pred_mask = extract_red_mask_as_array(red_mask_bytes)
            script_red_pixels = np.sum(pred_mask)
            area_metrics = compute_area_based_accuracy(script_red_pixels, red_area_from_screenshot_sqkm)
            
            
            # Print summary
            print(f"Accuracy Summary for ChangeMap ID {change_map_id}:")
            print(f"Script Red Area (sq km): {area_metrics['script_red_area_sqkm']}")
            print(f"Screenshot Red Area (sq km): {area_metrics['screenshot_red_area_sqkm']}")
            for key, value in area_metrics.items():
                if key not in ['script_red_area_sqkm', 'screenshot_red_area_sqkm']:
                    print(f"  {key}: {value}")
            
            # Save to TXT file
            txt_file = save_accuracy_to_txt(change_map_id, str(cm.from_date), str(cm.to_date), area_metrics)
            
            print(f"Full report: {txt_file}")
            
        

        db.commit()
        print(f"Water analysis completed for ChangeMap ID {change_map_id}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# ---------------- CLI ----------------
if __name__ == "__main__":
    change_map_id = 190  # Replace with your ChangeMap ID
    red_area_from_screenshot_sqkm = 0.014  # Replace with your screenshot red area in sq km
    run_water_analysis(change_map_id, red_area_from_screenshot_sqkm)