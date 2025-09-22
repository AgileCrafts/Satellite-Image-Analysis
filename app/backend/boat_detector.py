from inference_sdk import InferenceHTTPClient
import supervision as sv
import cv2
from matplotlib import pyplot as plt

# Create the client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="I5Ze1O0bcvMDOrhG1IFw"   # your API key
)

# Run inference on your image
result = CLIENT.infer("test5.png", model_id="sentinel-boat/1?confidence=0.01")

# Print results
# print(result)

image_path="test5.png"

image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Could not load {image_path}")

# Convert Roboflow result into Supervision detections
detections = sv.Detections.from_inference(result)

# Create a box annotator
annotator = sv.BoxAnnotator()

# Draw predictions
annotated_image = annotator.annotate(
    scene=image.copy(),
    detections=detections
)

# Show result using matplotlib (works everywhere)
plt.imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
plt.axis("off")
plt.show()

# Optionally save
cv2.imwrite("annotated_test5.png", annotated_image)