# water_analysis_db.py
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
import tifffile
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Image as ImageModel, ChangeMap  

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

    pre_mask = remove_small_objects(remove_small_holes(create_water_mask(pre_mndwi, pre_thresh), area_threshold=64), min_size=20)
    post_mask = remove_small_objects(remove_small_holes(create_water_mask(post_mndwi, post_thresh), area_threshold=64), min_size=20)

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

    buf = io.BytesIO()
    Image.fromarray(change_map_rgb).save(buf, format="PNG")
    buf.seek(0)
    return buf.read()

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

# ---------------- MAIN DB FUNCTION ----------------
def run_water_analysis(change_map_id: int):
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
        water_bytes = generate_water_change_map(pre_img.ndwi_data, post_img.ndwi_data)
        cm.water_analysis_image = water_bytes
        
        
        # Extract red-only overlay mask
        red_mask_bytes = extract_red_mask(water_bytes)
        # Overlay red mask on post-RGB image
        overlay_bytes = overlay_mask_on_rgb(post_img.rgb_data, water_bytes, alpha=0.6)
        cm.encroachment_overlay = overlay_bytes

        # Save overlay to file (e.g., for debugging)
        overlay_img = Image.open(io.BytesIO(overlay_bytes))
        overlay_img.save("encroachment_overlay.png")   # now you can open overlay_debug.png manually
        print("Overlay saved as overlay_debug.png")
        # Generate collage using RGB images from DB
        collage_bytes = create_image_collage(pre_img.rgb_data, post_img.rgb_data, water_bytes,
                                             str(cm.from_date), str(cm.to_date))
        cm.collage_image = collage_bytes

        db.commit()
        print(f"Water analysis completed for ChangeMap ID {change_map_id}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

# # ---------------- CLI ----------------
# if __name__ == "__main__":
#     change_map_id = int(input("Enter ChangeMap ID to perform water analysis: "))
#     run_water_analysis(change_map_id)
