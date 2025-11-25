# Required imports
from ultralytics import YOLO
import os
import torch

# Main execution block
if __name__ == "__main__":
    try:
        # Step 1: Load the pre-trained YOLOv8 model (nano version for speed)
        model = YOLO('yolov8n.pt')  # Downloads ~6MB if not present; pre-trained on COCO

        # Step 2: Define the path to your test image
        # Use one of your attached images or any local image
        test_image_path = 'test6.png'  # Update with the path to your first attached image
        # Alternatively, for the second image: './dredger_ground.jpg'
        # Ensure the image is in your project directory or provide full path

        # Step 3: Check if the image exists
        if not os.path.exists(test_image_path):
            print(f"Image not found at {test_image_path}. Please update the path or place the image in the project directory.")
        else:
            print(f"Running inference on {test_image_path}...")

            # Step 4: Run inference on the test image
            inference_results = model.predict(
                source=test_image_path,
                conf=0.01,  # Confidence threshold (adjust to 0.1-0.5 based on results)
                iou=0.45,   # IoU threshold for non-max suppression
                save=True,  # Saves the output image with detections
                save_txt=True  # Saves detection coordinates to a .txt file
            )

            # Step 5: Print and analyze results
            for result in inference_results:
                boxes = result.boxes.xyxy  # Bounding box coordinates
                scores = result.boxes.conf  # Confidence scores
                classes = result.boxes.cls  # Class IDs
                names = result.names  # Class names from COCO

                print("Detections:")
                for box, score, cls in zip(boxes, scores, classes):
                    class_name = names[int(cls)]
                    print(f"Class: {class_name}, Confidence: {score:.2f}, Box: {box}")

            # Step 6: Output location of saved results
            if os.path.exists('runs/detect/predict'):
                print(f"Results saved in runs/detect/predict. Check the folder for output images.")

    except Exception as e:
        print(f"An error occurred: {e}")

