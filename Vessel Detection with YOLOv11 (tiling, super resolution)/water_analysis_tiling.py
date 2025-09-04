import os
import json
import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont
import cv2
import torch
from ultralytics import YOLO
from skimage.filters import threshold_otsu

# -------------------- CONFIG --------------------
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.json')
    with open(config_path) as f:
        return json.load(f)

# -------------------- MNDWI --------------------
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band.astype(np.float32) + swir1_band.astype(np.float32)
    mndwi = np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)
    return mndwi

def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

# -------------------- LOAD SENTINEL-2 --------------------
def load_s2_bands(filepath):
    data = tifffile.imread(filepath)
    if data.ndim == 3 and data.shape[2] == 5:
        green_band = data[:, :, 0].astype(np.float32)  # B03
        red_band   = data[:, :, 1].astype(np.float32)  # B04
        nir_band   = data[:, :, 2].astype(np.float32)  # B08
        swir1_band = data[:, :, 3].astype(np.float32)  # B11
        scl_band   = data[:, :, 4]
        return green_band, red_band, nir_band, swir1_band, scl_band
    else:
        raise ValueError(f"Expected [H,W,5] (B03,B04,B08,B11,SCL). Got {data.shape}")

# -------------------- VESSEL DETECTION (YOLOv11 TILING) --------------------
def detect_and_remove_vessels(rgb_path, tiff_path, model_dir, output_dir,
                              conf=0.15, iou=0.4, patch_size=256, overlap=0.3, min_area=10):
    rgb_image = cv2.imread(rgb_path)
    if rgb_image is None:
        raise FileNotFoundError(f"RGB image not found at: {rgb_path}")
    rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB)
    h, w, _ = rgb_image.shape

    # Load YOLO model
    model_path = os.path.join(model_dir, "yolo11s_tci.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"YOLO model not found: {model_path}")
    model = YOLO(model_path)

    stride = int(patch_size * (1 - overlap))
    all_boxes = []

    for y in range(0, h, stride):
        for x in range(0, w, stride):
            y1, y2 = y, min(y + patch_size, h)
            x1, x2 = x, min(x + patch_size, w)
            patch = rgb_image[y1:y2, x1:x2]

            results = model.predict(
                source=patch,
                imgsz=max(patch.shape[:2]),
                conf=conf,
                iou=iou,
                device='cuda' if torch.cuda.is_available() else 'cpu'
            )

            for r in results:
                for box in r.boxes.xyxy.cpu().numpy():
                    # Map box coordinates back to original image
                    box[0] += x1
                    box[1] += y1
                    box[2] += x1
                    box[3] += y1
                    area = (box[2]-box[0])*(box[3]-box[1])
                    if area >= min_area:
                        all_boxes.append(box)

    valid_boxes = np.array(all_boxes)

    # Create vessel mask
    vessel_mask = np.ones(rgb_image.shape[:2], dtype=bool)
    for box in valid_boxes:
        x1, y1, x2, y2 = map(int, box)
        y1 = max(0, min(y1, vessel_mask.shape[0]-1))
        y2 = max(y1+1, min(y2, vessel_mask.shape[0]))
        x1 = max(0, min(x1, vessel_mask.shape[1]-1))
        x2 = max(x1+1, min(x2, vessel_mask.shape[1]))
        vessel_mask[y1:y2, x1:x2] = False

    # Resize vessel mask to match Sentinel bands
    green, red, nir, swir1, scl = load_s2_bands(tiff_path)
    vessel_mask = cv2.resize(vessel_mask.astype(np.uint8), (green.shape[1], green.shape[0]),
                             interpolation=cv2.INTER_NEAREST).astype(bool)

    # Mask the bands
    min_val = min(green.min(), red.min(), nir.min())
    cleaned_bands = [
        np.where(vessel_mask, green, min_val),
        np.where(vessel_mask, red, min_val),
        np.where(vessel_mask, nir, min_val),
        swir1.copy(),
        scl.copy()
    ]

    # Annotated RGB
    annotated_rgb = cv2.resize(rgb_image, (green.shape[1], green.shape[0]), interpolation=cv2.INTER_LINEAR)
    for box in valid_boxes:
        scale_x = green.shape[1] / rgb_image.shape[1]
        scale_y = green.shape[0] / rgb_image.shape[0]
        x1, y1, x2, y2 = map(int, [box[0]*scale_x, box[1]*scale_y, box[2]*scale_x, box[3]*scale_y])
        cv2.rectangle(annotated_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    os.makedirs(output_dir, exist_ok=True)
    annotated_path = os.path.join(output_dir, f"{os.path.basename(tiff_path).rsplit('.',1)[0]}_annotated.jpg")
    cv2.imwrite(annotated_path, cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))

    print(f"Annotated image saved to: {annotated_path}")
    print(f"Detected vessels: {len(valid_boxes)}")
    return valid_boxes, cleaned_bands, annotated_rgb

# -------------------- CHANGE DETECTION --------------------
def perform_change_detection(pre_image_path, post_image_path, model_dir, output_folder="change_maps"):
    pre_bands = load_s2_bands(pre_image_path)
    post_bands = load_s2_bands(post_image_path)

    pre_rgb_path  = os.path.join(output_folder, f"{os.path.basename(pre_image_path).rsplit('.',1)[0]}_RGB.jpg")
    post_rgb_path = os.path.join(output_folder, f"{os.path.basename(post_image_path).rsplit('.',1)[0]}_RGB.jpg")

    for rgb_path in [pre_rgb_path, post_rgb_path]:
        if not os.path.exists(rgb_path):
            raise FileNotFoundError(f"RGB image not found at: {rgb_path}")

    os.makedirs(output_folder, exist_ok=True)

    print("Removing vessels from pre-image...")
    pre_vessels, pre_cleaned_bands, pre_annotated = detect_and_remove_vessels(
        rgb_path=pre_rgb_path,
        tiff_path=pre_image_path,
        model_dir=model_dir,
        output_dir=output_folder
    )

    print("Removing vessels from post-image...")
    post_vessels, post_cleaned_bands, post_annotated = detect_and_remove_vessels(
        rgb_path=post_rgb_path,
        tiff_path=post_image_path,
        model_dir=model_dir,
        output_dir=output_folder
    )

    pre_mndwi  = calculate_mndwi(pre_cleaned_bands[0], pre_cleaned_bands[3])
    post_mndwi = calculate_mndwi(post_cleaned_bands[0], post_cleaned_bands[3])
    pre_mask  = create_water_mask(pre_mndwi,  threshold_otsu(pre_mndwi))
    post_mask = create_water_mask(post_mndwi, threshold_otsu(post_mndwi))

    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])
    pre_mask  = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    change_map_rgb[(pre_mask==0)&(post_mask==0)] = [128,128,128]  # land->land
    change_map_rgb[(pre_mask==1)&(post_mask==1)] = [0,0,255]      # water->water
    change_map_rgb[(pre_mask==0)&(post_mask==1)] = [0,255,0]      # new water
    change_map_rgb[(pre_mask==1)&(post_mask==0)] = [255,0,0]      # lost water

    output_filepath = os.path.join(output_folder, "water_change_map.png")
    Image.fromarray(change_map_rgb).save(output_filepath)
    print(f"Change map saved to: {output_filepath}")

    return output_filepath

# -------------------- IMAGE COLLAGE --------------------
def create_image_collage(pre_rgb_path, post_rgb_path, change_map_path, output_collage_path,
                         pre_date, post_date, change_date_range_str, label_font_path=None):
    img_pre = Image.open(pre_rgb_path).convert('RGB')
    img_post = Image.open(post_rgb_path).convert('RGB')
    img_change = Image.open(change_map_path).convert('RGB')

    width, height = img_pre.size
    font_size = max(20, int(height * 0.03 * 1.5))
    try:
        font = ImageFont.truetype(label_font_path, font_size) if label_font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text_padding = int(font_size * 0.2)
    _, _, _, text_height_approx = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), "A", font=font)
    total_width = (width * 3) + (text_padding * 4)
    total_height = height + text_height_approx + (text_padding * 3)
    collage = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(collage)

    labels = [
        f"Pre-Image (Original) - {pre_date}",
        f"Post-Image (Original) - {post_date}",
        f"Water Changes Detected ({change_date_range_str})"
    ]
    x_offset = text_padding
    y_offset_images = text_height_approx + (text_padding * 2)
    for img, label in zip([img_pre, img_post, img_change], labels):
        draw.text((x_offset, text_padding), label, font=font, fill=(0, 0, 0))
        collage.paste(img, (x_offset, y_offset_images))
        x_offset += width + text_padding
    collage.save(output_collage_path)
    print(f"Collage saved to: {output_collage_path}")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    cfg = load_config()
    analysis_settings = cfg['analysis_settings']

    pre_date = analysis_settings['pre_date']
    post_date = analysis_settings['post_date']
    downloads_base_path   = analysis_settings['downloads_base_path']
    wadownloads_base_path = analysis_settings['wadownloads_base_path']

    pre_image_ndwi_path  = os.path.join(downloads_base_path, pre_date,  f"{pre_date}.tiff")
    post_image_ndwi_path = os.path.join(downloads_base_path, post_date, f"{post_date}.tiff")
    output_wadownloads_folder = wadownloads_base_path
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

    for file_path in [pre_image_ndwi_path, post_image_ndwi_path]:
        if not os.path.exists(file_path):
            print(f"Error: Required file missing: {file_path}")
            raise SystemExit(1)

    print("\n--- Running Water Change Detection (YOLOv11 tiling) ---")
    generated_change_map_path = perform_change_detection(
        pre_image_path=pre_image_ndwi_path,
        post_image_path=post_image_ndwi_path,
        model_dir=model_dir,
        output_folder=output_wadownloads_folder
    )

    print("\n--- Running Image Collage Creation ---")
    pre_image_rgb_path  = os.path.join(output_wadownloads_folder, f"{pre_date}_RGB.jpg")
    post_image_rgb_path = os.path.join(output_wadownloads_folder, f"{post_date}_RGB.jpg")
    change_date_range_for_label = f"{pre_date} to {post_date}"
    collage_output_path = os.path.join(output_wadownloads_folder, "water_change_collage.png")

    create_image_collage(
        pre_rgb_path=pre_image_rgb_path,
        post_rgb_path=post_image_rgb_path,
        change_map_path=generated_change_map_path,
        output_collage_path=collage_output_path,
        pre_date=pre_date,
        post_date=post_date,
        change_date_range_str=change_date_range_for_label,
        label_font_path=None
    )

    print("\nAll tasks completed.")
