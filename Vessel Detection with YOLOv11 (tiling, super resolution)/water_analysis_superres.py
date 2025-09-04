import os
import json
import numpy as np
import tifffile
from PIL import Image, ImageDraw, ImageFont
import cv2
import torch
from ultralytics import YOLO
from skimage.filters import threshold_otsu
import matplotlib.pyplot as plt
from skimage.metrics import peak_signal_noise_ratio as psnr
import yaml

# Add satlas-super-resolution to system path (adjust to your cloned repo path)
import sys
sys.path.append('G:\\AgileCrafts\\Ver3 Satelite Image - Copy\\satlas-super-resolution')

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    print("Successfully imported RRDBNet from BasicSR")
except ImportError as e:
    print(f"Error importing BasicSR modules: {e}")
    print("Install BasicSR: pip install git+https://github.com/XPixelGroup/BasicSR.git")
    print("Ensure your virtual environment is activated")
    sys.exit(1)

# -------------------- CONFIG --------------------
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.json')
    with open(config_path) as f:
        return json.load(f)

# -------------------- MNDWI --------------------
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    mndwi = np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)
    return mndwi

def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

# -------------------- LOAD SENTINEL-2 --------------------
def load_s2_bands(filepath):
    data = tifffile.imread(filepath)
    if data.ndim == 3 and data.shape[2] == 5:
        green_band = data[:, :, 0]  # B03
        red_band = data[:, :, 1]    # B04
        nir_band = data[:, :, 2]    # B08
        swir1_band = data[:, :, 3]  # B11
        scl_band = data[:, :, 4]
        return green_band, red_band, nir_band, swir1_band, scl_band
    else:
        raise ValueError(f"Expected 5 bands, got {data.shape}")

# -------------------- SATLAS SUPER-RESOLUTION --------------------
def upscale_image_with_satlas(
    rgb_image,
    scale=4,
    weights_path=r'weights\1-S2-images\net_g_latest.pth',
    config_path=r'weights\1-S2-images\config.yml',
    tile=None,
    tile_pad=8
):
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Satlas weights not found: {weights_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Satlas config not found:  {config_path}")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # read config
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    if "network_g" not in cfg:
        raise KeyError("config.yml missing 'network_g' section (Satlas format expected).")
    g = cfg["network_g"]

    # build RRDBNet
    model = RRDBNet(
        num_in_ch=g.get("num_in_ch", 3),
        num_out_ch=g.get("num_out_ch", 3),
        num_feat=g.get("num_feat", 64),
        num_block=g.get("num_block", 23),
        num_grow_ch=g.get("num_grow_ch", 32),
        scale=g.get("scale", scale),
    ).to(device)

    # load checkpoint
    ckpt = torch.load(weights_path, map_location=device)
    state = None
    for k in ["params_ema", "params", "state_dict", "net_g", "model"]:
        if k in ckpt and isinstance(ckpt[k], dict):
            state = ckpt[k]
            break
    if state is None and isinstance(ckpt, dict):
        state = ckpt
    def strip_prefix(sd, prefix="module."):
        return { (k[len(prefix):] if k.startswith(prefix) else k): v for k, v in sd.items() }
    state = strip_prefix(state, "module.")
    model.load_state_dict(state, strict=True)
    model.eval()

    img = rgb_image.astype(np.float32) / 255.0
    img = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).to(device)

    @torch.no_grad()
    def run_net(x):
        return model(x).clamp_(0, 1)

    if tile is None:
        with torch.no_grad():
            out = run_net(img)
    else:
        b, c, h, w = img.shape
        sf = g.get("scale", scale)
        out = torch.zeros((b, c, h*sf, w*sf), device=device)
        weight = torch.zeros_like(out)
        step = tile - tile_pad*2
        for y in range(0, h, step):
            for x in range(0, w, step):
                y0 = max(y - tile_pad, 0)
                x0 = max(x - tile_pad, 0)
                y1 = min(y + tile + tile_pad, h)
                x1 = min(x + tile + tile_pad, w)
                patch = img[:, :, y0:y1, x0:x1]
                pred  = run_net(patch)
                oy0 = y0*sf; ox0 = x0*sf
                oy1 = y1*sf; ox1 = x1*sf
                out[:, :, oy0:oy1, ox0:ox1] += pred
                weight[:, :, oy0:oy1, ox0:ox1] += 1.0
        out /= weight

    sr = (out.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255.0).round().astype(np.uint8)

    debug_path = os.path.join(os.path.dirname(weights_path), 'debug_super_res.jpg')
    cv2.imwrite(debug_path, cv2.cvtColor(sr, cv2.COLOR_RGB2BGR))
    print(f"[Satlas SR] saved debug: {debug_path}")
    return sr

# -------------------- VESSEL DETECTION --------------------
def detect_and_remove_vessels(rgb_path, tiff_path, model_dir, output_dir, apply_sr=True, sr_scale=4):
    if not os.path.exists(rgb_path):
        raise FileNotFoundError(f"RGB image not found at: {rgb_path}")
    rgb_image = cv2.imread(rgb_path)
    rgb_image = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB)
    original_shape = rgb_image.shape[:2]

    # Pre-super-resolution debug
    debug_pre_sr_path = os.path.join(output_dir, f"{os.path.basename(tiff_path).rsplit('.', 1)[0]}_pre_sr.jpg")
    cv2.imwrite(debug_pre_sr_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    print(f"Pre-super-resolution image saved to: {debug_pre_sr_path}")

    # Apply Satlas SR
    if apply_sr:
        print(f"Applying Super-Resolution (Satlas 1-S2, x{sr_scale})...")
        sr_weights = os.path.join(os.path.dirname(__file__), r"weights\1-S2-images\net_g_latest.pth")
        sr_config  = os.path.join(os.path.dirname(__file__), r"weights\1-S2-images\config.yml")
        rgb_image = upscale_image_with_satlas(rgb_image, scale=sr_scale, weights_path=sr_weights, config_path=sr_config)

        super_res_path = os.path.join(output_dir, f"{os.path.basename(tiff_path).rsplit('.', 1)[0]}_super_res.jpg")
        cv2.imwrite(super_res_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
        print(f"Super-resolved image saved to: {super_res_path}")

    model_path = os.path.join(model_dir, "yolo11s_tci.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"YOLO model not found: {model_path}")
    model = YOLO(model_path)

    results = model.predict(
        source=rgb_image,
        imgsz=rgb_image.shape[:2],
        conf=0.25,
        iou=0.45,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )

    valid_boxes = []
    for r in results:
        for box in r.boxes.xyxy.cpu().numpy():
            valid_boxes.append(box)
    valid_boxes = np.array(valid_boxes)

    vessel_mask = np.ones(rgb_image.shape[:2], dtype=bool)
    for box in valid_boxes:
        x1, y1, x2, y2 = map(int, box)
        y1 = max(0, min(y1, vessel_mask.shape[0]-1))
        y2 = max(y1+1, min(y2, vessel_mask.shape[0]))
        x1 = max(0, min(x1, vessel_mask.shape[1]-1))
        x2 = max(x1+1, min(x2, vessel_mask.shape[1]))
        vessel_mask[y1:y2, x1:x2] = False

    bands = load_s2_bands(tiff_path)
    green, red, nir, swir1, scl = bands
    original_shape = green.shape

    vessel_mask = cv2.resize(
        vessel_mask.astype(np.uint8),
        (original_shape[1], original_shape[0]),
        interpolation=cv2.INTER_NEAREST
    ).astype(bool)

    min_val = min(green.min(), red.min(), nir.min())
    cleaned_bands = [
        np.where(vessel_mask, green, min_val),
        np.where(vessel_mask, red, min_val),
        np.where(vessel_mask, nir, min_val),
        swir1.copy(),
        scl.copy()
    ]

    annotated_rgb = cv2.resize(rgb_image, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_LINEAR)
    for box in valid_boxes:
        scale_x = original_shape[1] / rgb_image.shape[1]
        scale_y = original_shape[0] / rgb_image.shape[0]
        x1, y1, x2, y2 = map(int, [box[0]*scale_x, box[1]*scale_y, box[2]*scale_x, box[3]*scale_y])
        x1 = max(0, min(x1, annotated_rgb.shape[1]-1))
        x2 = max(x1+1, min(x2, annotated_rgb.shape[1]))
        y1 = max(0, min(y1, annotated_rgb.shape[0]-1))
        y2 = max(y1+1, min(y2, annotated_rgb.shape[0]))
        cv2.rectangle(annotated_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(tiff_path).rsplit(".", 1)[0]
    annotated_path = os.path.join(output_dir, f"{base_name}_annotated.jpg")
    cv2.imwrite(annotated_path, cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))

    print(f"Detected vessels: {len(valid_boxes)}")
    print(f"Annotated image saved to: {annotated_path}")

    return valid_boxes, cleaned_bands, annotated_rgb

# -------------------- CHANGE DETECTION --------------------
def perform_change_detection(pre_image_path, post_image_path, model_dir, output_folder="change_maps"):
    pre_bands = load_s2_bands(pre_image_path)
    post_bands = load_s2_bands(post_image_path)

    pre_rgb_path = r"G:\AgileCrafts\Ver3 Satelite Image - Copy\wadownloads\2024-10-22_RGB.jpg"
    post_rgb_path = r"G:\AgileCrafts\Ver3 Satelite Image - Copy\wadownloads\2025-05-10_RGB.jpg"

    for rgb_path in [pre_rgb_path, post_rgb_path]:
        if not os.path.exists(rgb_path):
            raise FileNotFoundError(f"RGB image not found at: {rgb_path}")

    print("Removing vessels from pre-image...")
    pre_vessels, pre_cleaned_bands, pre_annotated = detect_and_remove_vessels(pre_rgb_path, pre_image_path, model_dir, output_folder, apply_sr=True, sr_scale=4)
    print("Removing vessels from post-image...")
    post_vessels, post_cleaned_bands, post_annotated = detect_and_remove_vessels(post_rgb_path, post_image_path, model_dir, output_folder, apply_sr=True, sr_scale=4)

    pre_mndwi = calculate_mndwi(pre_cleaned_bands[0], pre_cleaned_bands[3])
    post_mndwi = calculate_mndwi(post_cleaned_bands[0], post_cleaned_bands[3])
    pre_mask = create_water_mask(pre_mndwi, threshold_otsu(pre_mndwi))
    post_mask = create_water_mask(post_mndwi, threshold_otsu(post_mndwi))

    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])
    pre_mask = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    change_map_rgb[(pre_mask==0)&(post_mask==0)] = [128,128,128]  # No change land
    change_map_rgb[(pre_mask==1)&(post_mask==1)] = [0,0,255]      # Persistent water
    change_map_rgb[(pre_mask==0)&(post_mask==1)] = [0,255,0]      # New water
    change_map_rgb[(pre_mask==1)&(post_mask==0)] = [255,0,0]      # Lost water

    os.makedirs(output_folder, exist_ok=True)
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
    except:
        font = ImageFont.load_default()

    text_padding = int(font_size*0.2)
    _, _, text_width, text_height_approx = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0,0),"A",font=font)
    total_width = (width*3) + (text_padding*4)
    total_height = height + text_height_approx + (text_padding*3)
    collage = Image.new('RGB', (total_width, total_height), color=(255,255,255))
    draw = ImageDraw.Draw(collage)

    labels = [
        f"Pre-Image (Original) - {pre_date}",
        f"Post-Image (Original) - {post_date}",
        f"Water Changes Detected ({change_date_range_str})"
    ]
    x_offset = text_padding
    y_offset_images = text_height_approx + (text_padding*2)
    for img, label in zip([img_pre, img_post, img_change], labels):
        draw.text((x_offset, text_padding), label, font=font, fill=(0,0,0))
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
    downloads_base_path = analysis_settings['downloads_base_path']
    wadownloads_base_path = analysis_settings['wadownloads_base_path']

    pre_image_ndwi_path = os.path.join(downloads_base_path, pre_date, f"{pre_date}.tiff")
    post_image_ndwi_path = os.path.join(downloads_base_path, post_date, f"{post_date}.tiff")
    output_wadownloads_folder = wadownloads_base_path
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

    for file_path in [pre_image_ndwi_path, post_image_ndwi_path]:
        if not os.path.exists(file_path):
            print(f"Error: Required file missing: {file_path}")
            exit(1)

    print("\n--- Running Water Change Detection ---")
    generated_change_map_path = perform_change_detection(
        pre_image_path=pre_image_ndwi_path,
        post_image_path=post_image_ndwi_path,
        model_dir=model_dir,
        output_folder=output_wadownloads_folder
    )

    print("\n--- Running Image Collage Creation ---")
    pre_image_rgb_path = os.path.join(wadownloads_base_path, f"{pre_date}_RGB.jpg")
    post_image_rgb_path = os.path.join(wadownloads_base_path, f"{post_date}_RGB.jpg")
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
