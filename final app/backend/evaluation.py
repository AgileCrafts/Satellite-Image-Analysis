# import rasterio
# from rasterio.enums import Resampling
# import numpy as np
# from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, jaccard_score

# def evaluate_binary_mask(pred_tif_path, gt_tif_path):
#     """
#     Compare predicted binary mask with ground-truth mask and compute metrics.

#     Args:
#         pred_tif_path (str): Path to predicted mask GeoTIFF (0/255 or 0/1).
#         gt_tif_path (str): Path to ground-truth mask GeoTIFF (0/255 or 0/1).

#     Returns:
#         dict: Accuracy, Precision, Recall, F1 Score, IoU
#     """

#     # Load ground-truth mask
#     with rasterio.open(gt_tif_path) as src_gt:
#         gt_mask = src_gt.read(1)
    
#     # Load predicted mask and resample to match GT size
#     with rasterio.open(pred_tif_path) as src_pred:
#         pred_mask = src_pred.read(
#             1,
#             out_shape=(gt_mask.shape[0], gt_mask.shape[1]),
#             resampling=Resampling.nearest
#         )

#     # Convert both masks to binary 0/1
#     gt_bin = (gt_mask > 0).astype(np.uint8)
#     pred_bin = (pred_mask > 0).astype(np.uint8)

#     # Flatten for sklearn metrics
#     gt_flat = gt_bin.flatten()
#     pred_flat = pred_bin.flatten()

#     # Compute metrics
#     metrics = {
#         "Accuracy": accuracy_score(gt_flat, pred_flat),
#         "Precision": precision_score(gt_flat, pred_flat, zero_division=0),
#         "Recall": recall_score(gt_flat, pred_flat, zero_division=0),
#         "F1 Score": f1_score(gt_flat, pred_flat, zero_division=0),
#         "IoU": jaccard_score(gt_flat, pred_flat, zero_division=0)
#     }

#     return metrics


# pred_path = "lost_water_mask.tif"
# gt_path = "real_mask.tif"

# metrics = evaluate_binary_mask(pred_path, gt_path)

# for k, v in metrics.items():
#     print(f"{k}: {v:.3f}")
    
    
    
import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, jaccard_score
from skimage.transform import resize

def align_and_evaluate_masks(pred_tif_path, gt_tif_path, visualize=True):
    """
    Align predicted mask and GT mask, visualize, and compute metrics.
    Resamples predicted mask to match GT if needed.
    """
    # Load GT mask
    with rasterio.open(gt_tif_path) as src_gt:
        gt_mask = src_gt.read(1)
        gt_transform = src_gt.transform
        gt_crs = src_gt.crs
        gt_bounds = src_gt.bounds
        gt_res = src_gt.res
        gt_shape = gt_mask.shape

    # Load Predicted mask
    with rasterio.open(pred_tif_path) as src_pred:
        pred_crs = src_pred.crs
        pred_mask = src_pred.read(1)

        # Resample predicted mask to GT shape if different
        if pred_mask.shape != gt_shape:
            pred_mask_resampled = src_pred.read(
                1,
                out_shape=gt_shape,
                resampling=Resampling.nearest
            )
        else:
            pred_mask_resampled = pred_mask

    # Convert both masks to binary (0/1)
    gt_bin = (gt_mask > 0).astype(np.uint8)
    pred_bin = (pred_mask_resampled > 0).astype(np.uint8)
    ground_truth = mpimg.imread("demo.png")
    ground_truth = resize(ground_truth, pred_bin.shape, anti_aliasing=True)
    
    # Visualization
    if visualize:
        plt.figure(figsize=(12, 6))
        plt.imshow(ground_truth, cmap='gray', alpha=0.6)  # Ground truth with partial transparency
        plt.imshow(pred_bin, cmap='gray', alpha=0.6)  # Predicted mask overlaid
        plt.title("Overlay of Ground Truth and Predicted Mask (Resampled)")
        plt.show()

    # Flatten for metrics
    gt_flat = gt_bin.flatten()
    pred_flat = pred_bin.flatten()

    # Confusion matrix counts
    tn, fp, fn, tp = confusion_matrix(gt_flat, pred_flat, labels=[0,1]).ravel()

    # Metrics in %
    acc = accuracy_score(gt_flat, pred_flat) * 100
    prec = precision_score(gt_flat, pred_flat, zero_division=0) * 100
    rec = recall_score(gt_flat, pred_flat, zero_division=0) * 100
    f1 = f1_score(gt_flat, pred_flat, zero_division=0) * 100
    iou = jaccard_score(gt_flat, pred_flat, zero_division=0) * 100

    # Print results
    print("=== Confusion Matrix Counts ===")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}\n")
    print("=== Metrics (in %) ===")
    print(f"Accuracy: {acc:.2f}%")
    print(f"Precision: {prec:.2f}%")
    print(f"Recall: {rec:.2f}%")
    print(f"F1 Score: {f1:.2f}%")
    print(f"IoU: {iou:.2f}%")

    return {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "Accuracy": acc, "Precision": prec, "Recall": rec,
        "F1": f1, "IoU": iou
    }

# === USAGE ===
pred_path = "lost_water_mask.tif"
gt_path = "real_mask.tif"

metrics = align_and_evaluate_masks(pred_path, gt_path, visualize=True)
