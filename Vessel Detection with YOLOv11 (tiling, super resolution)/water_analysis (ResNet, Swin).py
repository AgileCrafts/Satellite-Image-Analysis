import numpy as np
import tifffile
import os
import json
from PIL import Image, ImageDraw, ImageFont
from skimage.filters import threshold_otsu
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.backbone_utils import BackboneWithFPN
import cv2
import rasterio
from pathlib import Path

# Function to load configuration from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.json')
    with open(config_path) as f:
        return json.load(f)

# Function to calculate MNDWI
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    mndwi = np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)
    return mndwi

# Function to create a binary water mask
def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold

# Function to load Sentinel-2 TIFFs (B03, B04, B08, B11, SCL)
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
            raise ValueError(f"Expected 5 bands (B03, B04, B08, B11, SCL) in TIFF, but got shape {data.shape}")
    except Exception as e:
        print(f"Error loading TIFF file {filepath}: {e}")
        raise

# Function to preprocess TIFF for direct inference
# def preprocess_tiff_for_inference(tiff_path, output_dir):
#     """Convert TIFF to TCI-like RGB (B04, B03, B08) for inference."""
#     output_dir = Path(output_dir)
#     output_dir.mkdir(exist_ok=True)
#     output_tiff = output_dir / f"preprocessed_{Path(tiff_path).stem}.tif"

#     with rasterio.open(tiff_path) as src:
#         profile = src.profile
#         red, green, nir = src.read([2, 1, 3])
#         rgb = np.stack([red, green, nir], axis=0).astype(np.float32)
#         profile.update(driver='GTiff')
#         with rasterio.open(output_tiff, 'w', **profile) as dst:
#             dst.write(rgb)
#     return str(output_tiff)


def detect_and_remove_vessels(band_data, tiff_path, model_dir, output_dir):
    """
    Detect and remove vessels from Sentinel-2 bands.

    Args:
        band_data (tuple): Tuple of (green, red, nir, swir1, scl) bands as numpy arrays.
        tiff_path (str): Path to the original TIFF for preprocessing and naming output files.
        model_dir (str): Directory containing model weights.
        output_dir (str): Folder to save annotated images.

    Returns:
        valid_boxes (np.ndarray): Detected vessel bounding boxes.
        cleaned_bands (list): List of cleaned bands [green, red, nir, swir1, scl].
        annotated_rgb (np.ndarray): RGB image with bounding boxes drawn.
    """
    import os
    import torch
    import torchvision
    import numpy as np
    import cv2
    import rasterio
    from torchvision.models.detection import FasterRCNN, fasterrcnn_resnet50_fpn
    from torchvision.models.detection.backbone_utils import resnet_fpn_backbone

    green, red, nir, swir1, scl = band_data
    rgb_image = np.stack([red, green, nir], axis=-1).astype(np.uint8)  # TCI-like RGB (B04, B03, B08)

    # Ensure output_dir is a directory
    os.makedirs(output_dir, exist_ok=True)

    # Load model
    model_path = os.path.join(model_dir, "swin_v2_s-637d8ceb.pth")
    fallback_model_path = os.path.join(model_dir, "resnet50-0676ba61.pth")

    try:
        print(f"Attempting to load model from {model_path}")
        state_dict = torch.load(model_path, map_location='cpu')
        state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
        model = fasterrcnn_resnet50_fpn(weights=None, num_classes=2)  # 2 classes: background + vessel
        model.load_state_dict(state_dict)
        print(f"Loaded {model_path} as full Faster R-CNN model.")
    except Exception as e:
        print(f"Failed to load {model_path}: {e}. Falling back to ResNet50.")
        if not os.path.exists(fallback_model_path):
            raise FileNotFoundError(f"Fallback model weights not found at {fallback_model_path}")
        try:
            state_dict = torch.load(fallback_model_path, map_location='cpu')
            state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
            backbone = resnet_fpn_backbone('resnet50', pretrained=False)
            try:
                backbone.load_state_dict(state_dict)
            except Exception as e:
                print(f"Failed to load {fallback_model_path} into backbone: {e}. Trying as full model.")
                model = FasterRCNN(backbone, num_classes=2)
                model.load_state_dict(state_dict)
            else:
                model = FasterRCNN(backbone, num_classes=2)
            print(f"Loaded {fallback_model_path} as ResNet50 backbone.")
        except Exception as e:
            raise RuntimeError(f"Failed to load fallback model: {e}")

    model.eval()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    # Preprocess image for inference
    with rasterio.open(tiff_path) as src:
        img = src.read([2, 1, 3]).transpose(1, 2, 0)  # RGB (B04, B03, B08)
    img = img.astype(np.float32) / 65535.0  # Normalize to [0, 1]
    img_tensor = torch.from_numpy(img).permute(2, 0, 1).to(device)
    normalize = torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    img_tensor = normalize(img_tensor).unsqueeze(0)

    # Run inference
    with torch.no_grad():
        prediction = model(img_tensor)

    boxes = prediction[0]['boxes'].cpu().numpy()
    scores = prediction[0]['scores'].cpu().numpy()
    threshold = 0.9
    valid_boxes = boxes[scores > threshold]

    # Create vessel mask
    vessel_mask = np.ones_like(green, dtype=bool)
    for box in valid_boxes:
        x1, y1, x2, y2 = map(int, box)
        y1 = max(0, min(y1, green.shape[0] - 1))
        y2 = max(y1 + 1, min(y2, green.shape[0]))
        x1 = max(0, min(x1, green.shape[1] - 1))
        x2 = max(x1 + 1, min(x2, green.shape[1]))
        vessel_mask[y1:y2, x1:x2] = False

    # Apply mask to bands
    cleaned_bands = [
        np.where(vessel_mask, green, green.min()),
        np.where(vessel_mask, red, red.min()),
        np.where(vessel_mask, nir, nir.min()),
        swir1.copy(),
        scl.copy()
    ]

    # Annotate RGB for visualization
    annotated_rgb = rgb_image.copy()
    for box in valid_boxes:
        x1, y1, x2, y2 = map(int, box)
        x1 = max(0, min(x1, annotated_rgb.shape[1] - 1))
        x2 = max(x1 + 1, min(x2, annotated_rgb.shape[1]))
        y1 = max(0, min(y1, annotated_rgb.shape[0] - 1))
        y2 = max(y1 + 1, min(y2, annotated_rgb.shape[0]))
        cv2.rectangle(annotated_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Save annotated image
    base_name = os.path.basename(tiff_path).rsplit(".", 1)[0]
    annotated_path = os.path.join(output_dir, f"{base_name}_annotated.jpg")
    cv2.imwrite(annotated_path, cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))

    print(f"Detected vessels: {len(valid_boxes)}")
    print(f"Annotated image saved to: {annotated_path}")

    return valid_boxes, cleaned_bands, annotated_rgb



# Function to perform change detection and save the change map
def perform_change_detection(pre_image_path, post_image_path, model_dir, output_folder="change_maps"):
    print(f"Loading pre-image: {pre_image_path}")
    pre_green, pre_red, pre_nir, pre_swir1, pre_scl = load_s2_bands(pre_image_path)
    print(f"Loading post-image: {post_image_path}")
    post_green, post_red, post_nir, post_swir1, post_scl = load_s2_bands(post_image_path)
    
    print("Detecting and removing vessels in pre-image...")
    pre_vessels, pre_cleaned_bands, pre_annotated = detect_and_remove_vessels(
        (pre_green, pre_red, pre_nir, pre_swir1, pre_scl), pre_image_path, model_dir, output_folder
    )
    print("Detecting and removing vessels in post-image...")
    post_vessels, post_cleaned_bands, post_annotated = detect_and_remove_vessels(
        (post_green, post_red, post_nir, post_swir1, post_scl), post_image_path, model_dir, output_folder
    )
    
    # Unpack cleaned bands
    pre_cleaned_green, pre_cleaned_red, pre_cleaned_nir, pre_cleaned_swir1, pre_cleaned_scl = pre_cleaned_bands
    post_cleaned_green, post_cleaned_red, post_cleaned_nir, post_cleaned_swir1, post_cleaned_scl = post_cleaned_bands
    
    # Calculate MNDWI
    print("Calculating MNDWI for pre-image...")
    pre_mndwi = calculate_mndwi(pre_cleaned_green, pre_cleaned_swir1)
    print("Calculating MNDWI for post-image...")
    post_mndwi = calculate_mndwi(post_cleaned_green, post_cleaned_swir1)
    
    print("Applying MNDWI threshold: Adaptive threshold to create water masks.")
    pre_thresh = threshold_otsu(pre_mndwi)
    post_thresh = threshold_otsu(post_mndwi)
    
    pre_mask = create_water_mask(pre_mndwi, threshold=pre_thresh)
    post_mask = create_water_mask(post_mndwi, threshold=post_thresh)
    
    if pre_mask.shape != post_mask.shape:
        print("Warning: Pre and post image masks have different shapes. Aligning to smallest dimensions.")
        min_rows = min(pre_mask.shape[0], post_mask.shape[0])
        min_cols = min(pre_mask.shape[1], post_mask.shape[1])
        pre_mask = pre_mask[:min_rows, :min_cols]
        post_mask = post_mask[:min_rows, :min_cols]
    
    print("Performing change detection...")
    pre_mask_int = pre_mask.astype(np.uint8)
    post_mask_int = post_mask.astype(np.uint8)
    
    change_map_rgb = np.zeros((pre_mask.shape[0], pre_mask.shape[1], 3), dtype=np.uint8)
    
    COLOR_PERSISTENT_WATER = [0, 0, 255]  # Blue
    COLOR_NEW_WATER = [0, 255, 0]  # Green
    COLOR_LOST_WATER = [255, 0, 0]  # Red
    COLOR_NO_CHANGE_LAND = [128, 128, 128]  # Gray
    
    no_change_land_mask = (pre_mask_int == 0) & (post_mask_int == 0)
    change_map_rgb[no_change_land_mask] = COLOR_NO_CHANGE_LAND
    persistent_water_mask = (pre_mask_int == 1) & (post_mask_int == 1)
    change_map_rgb[persistent_water_mask] = COLOR_PERSISTENT_WATER
    new_water_mask = (pre_mask_int == 0) & (post_mask_int == 1)
    change_map_rgb[new_water_mask] = COLOR_NEW_WATER
    lost_water_mask = (pre_mask_int == 1) & (post_mask_int == 0)
    change_map_rgb[lost_water_mask] = COLOR_LOST_WATER
    
    os.makedirs(output_folder, exist_ok=True)
    
    pre_date_str = os.path.basename(os.path.dirname(pre_image_path))
    post_date_str = os.path.basename(os.path.dirname(post_image_path))
    output_filename = f"edited_water_change_map_{pre_date_str}_to_{post_date_str}.png"
    output_filepath = os.path.join(output_folder, output_filename)
    
    print(f"Saving change map to: {output_filepath}")
    
    # Save cleaned and annotated RGB images
    pre_cleaned_rgb = np.stack([pre_cleaned_red, pre_cleaned_green, pre_cleaned_nir], axis=-1).astype(np.uint8)
    post_cleaned_rgb = np.stack([post_cleaned_red, post_cleaned_green, post_cleaned_nir], axis=-1).astype(np.uint8)
    cv2.imwrite(os.path.join(output_folder, f"{pre_date_str}_cleaned_RGB.jpg"), cv2.cvtColor(pre_cleaned_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(output_folder, f"{post_date_str}_cleaned_RGB.jpg"), cv2.cvtColor(post_cleaned_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(output_folder, f"{pre_date_str}_annotated_RGB.jpg"), cv2.cvtColor(pre_annotated, cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(output_folder, f"{post_date_str}_annotated_RGB.jpg"), cv2.cvtColor(post_annotated, cv2.COLOR_RGB2BGR))
    
    Image.fromarray(change_map_rgb).save(output_filepath)
    print("Water change detection and map generation complete!")
    return output_filepath

# Function for creating the collage
def create_image_collage(pre_rgb_path, post_rgb_path, change_map_path, output_collage_path,
                         pre_date, post_date, change_date_range_str, label_font_path=None):
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
            print("Warning: Custom font not found. Using default Pillow font.")
    except Exception as e:
        print(f"Error loading font: {e}. Using default Pillow font.")
        font = ImageFont.load_default()
    
    _, _, text_width, text_height_approx = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0,0), "A", font=font)
    text_padding = int(font_size * 0.2)
    
    total_width = (width * 3) + (text_padding * 4)
    total_height = height + text_height_approx + (text_padding * 3)
    
    collage = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(collage)
    
    x_offset = text_padding
    y_offset_images = text_height_approx + (text_padding * 2)
    
    draw.text((x_offset, text_padding), label_pre, font=font, fill=(0, 0, 0))
    collage.paste(img_pre, (x_offset, y_offset_images))
    
    x_offset += width + text_padding
    draw.text((x_offset, text_padding), label_post, font=font, fill=(0, 0, 0))
    collage.paste(img_post, (x_offset, y_offset_images))
    
    x_offset += width + text_padding
    draw.text((x_offset, text_padding), label_change, font=font, fill=(0, 0, 0))
    collage.paste(img_change, (x_offset, y_offset_images))
    
    collage.save(output_collage_path)
    print(f"Collage saved to: {output_collage_path}")

if __name__ == "__main__":
    # LOAD CONFIGURATION
    cfg = load_config()
    analysis_settings = cfg['analysis_settings']
    
    # Retrieve dates and paths from config
    pre_date = analysis_settings['pre_date']
    post_date = analysis_settings['post_date']
    downloads_base_path = analysis_settings['downloads_base_path']
    wadownloads_base_path = analysis_settings['wadownloads_base_path']
    
    # DYNAMICALLY CONSTRUCT PATHS
    pre_image_ndwi_path = os.path.join(downloads_base_path, pre_date, f"{pre_date}.tiff")
    post_image_ndwi_path = os.path.join(downloads_base_path, post_date, f"{post_date}.tiff")
    output_wadownloads_folder = wadownloads_base_path
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    
    
    # VALIDATE INPUT FILES
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
    
    pre_date_for_label = pre_date
    post_date_for_label = post_date
    change_date_range_for_label = f"{pre_date_for_label} to {post_date_for_label}"
    
    collage_output_path = os.path.join(output_wadownloads_folder, "water_change_collage.png")
    
    font_file_path = None
    
    create_image_collage(
        pre_rgb_path=pre_image_rgb_path,
        post_rgb_path=post_image_rgb_path,
        change_map_path=generated_change_map_path,
        output_collage_path=collage_output_path,
        pre_date=pre_date_for_label,
        post_date=post_date_for_label,
        change_date_range_str=change_date_range_for_label,
        label_font_path=font_file_path
    )
    
    print("\nAll tasks completed. Check your 'wadownloads' folder for results.")