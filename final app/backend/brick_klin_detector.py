from inference_sdk import InferenceHTTPClient
import supervision as sv
import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
from matplotlib import pyplot as plt

# === CONFIGURATION ===
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="I5Ze1O0bcvMDOrhG1IFw"
)

MAPBOX_TOKEN = "pk.eyJ1IjoicnViYXlldHJhaXNhIiwiYSI6ImNtZmYxNjVyNzBkY3cya29hd3JwcHgxem8ifQ.9EWRZl8FOkbvcz5aVBDOpg"
longitude, latitude = 90.08686, 22.16186
zoom, width, height = 17, 1280, 1280
style = "satellite-streets-v12"

# Build URL
url = (
    f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
    f"{longitude},{latitude},{zoom}/{width}x{height}@2x"
    f"?access_token={MAPBOX_TOKEN}"
)

# === DOWNLOAD IMAGE FROM MAPBOX ===
response = requests.get(url)
if response.status_code != 200:
    raise RuntimeError(f"Failed to fetch image: {response.status_code}, {response.text}")

pil_image = Image.open(BytesIO(response.content)).convert("RGB")

# Convert PIL → OpenCV (for visualization later)
image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# === RUN INFERENCE (directly pass PIL Image) ===
result = CLIENT.infer(pil_image, model_id="brick-kiln-detection-golrh/1")

# === CONVERT RESULTS TO SUPERVISION DETECTIONS ===
detections = sv.Detections.from_inference(result)

# Build labels with class name + confidence %
labels = [
    f"{detections.data['class_name'][i]} {detections.confidence[i]*100:.1f}%"
    for i in range(len(detections))
]

# Create annotators
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

# Draw bounding boxes
annotated_image = box_annotator.annotate(
    scene=image.copy(),
    detections=detections
)

# Draw labels
annotated_image = label_annotator.annotate(
    scene=annotated_image,
    detections=detections,
    labels=labels
)

# === SHOW ===
plt.imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
plt.axis("off")
plt.show()
cv2.imwrite("annotated_mapbox.png", annotated_image)