# # check.py

# import io
# import matplotlib.pyplot as plt
# import tifffile
# from sqlalchemy.orm import Session
# from models import Image
# from database import SessionLocal


# def view_rgb_image_from_db(image_id: int):
#     db: Session = SessionLocal()
#     try:
#         image = db.query(Image).filter(Image.id == image_id).first()
#         if not image:
#             print(f"No image found with id={image_id}")
#             return

#         if not image.rgb_data:
#             print(f"No RGB data found for image id={image_id}")
#             return

#         # Read TIFF data from in-memory bytes
#         rgb_array = tifffile.imread(io.BytesIO(image.rgb_data))

#         # Show with matplotlib
#         plt.figure(figsize=(8, 8))
#         plt.imshow(rgb_array)
#         plt.title(f"RGB Image ID {image_id}")
#         plt.axis('off')
#         plt.show()

#     finally:
#         db.close()


# if __name__ == "__main__":
#     image_id = 4 # 🔁 Change this to any existing image ID in your DB
#     view_rgb_image_from_db(image_id)


# import io
# import matplotlib.pyplot as plt
# from PIL import Image as PILImage
# from sqlalchemy.orm import Session
# from models import ChangeMap
# from database import SessionLocal

# def view_image_from_db(image_bytes: bytes, title: str):
#     if not image_bytes:
#         print(f"No image data found for {title}")
#         return
    
#     # Read the image bytes into a PIL Image object
#     image = PILImage.open(io.BytesIO(image_bytes))

#     # Display the image
#     plt.figure(figsize=(10, 8))
#     plt.imshow(image)
#     plt.title(title)
#     plt.axis('off')
#     plt.show()

# def view_water_analysis_and_collage(change_map_id: int):
#     db: Session = SessionLocal()
#     try:
#         # Retrieve the ChangeMap record by ID
#         change_map = db.query(ChangeMap).filter(ChangeMap.id == change_map_id).first()
#         if not change_map:
#             print(f"No ChangeMap found with id={change_map_id}")
#             return

#         # Display the Water Analysis Image
#         print(f"Displaying Water Analysis Image for ChangeMap ID {change_map_id}...")
#         view_image_from_db(change_map.water_analysis_image, "Water Analysis Image")

#         # Display the Collage Image
#         print(f"Displaying Collage Image for ChangeMap ID {change_map_id}...")
#         view_image_from_db(change_map.collage_image, "Collage Image")

#     finally:
#         db.close()

# if __name__ == "__main__":
#     change_map_id = 2  # Change this to the ID of the ChangeMap you want to view
#     view_water_analysis_and_collage(change_map_id)


from PIL import Image
import numpy as np

def count_red_area(image_path, pixel_resolution_m=10):
    # Load image
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img)

    # Define red pixel threshold
    # Adjust these values if needed
    red_mask = (arr[:,:,0] > 150) & (arr[:,:,1] < 80) & (arr[:,:,2] < 80)

    # Count red pixels
    red_pixel_count = np.sum(red_mask)

    # Calculate area in square kilometers
    area_sq_km = red_pixel_count * (pixel_resolution_m ** 2) / 1_000_000

    return red_pixel_count, area_sq_km

if __name__ == "__main__":
    image_path = "copy.png"  # Replace with your screenshot path
    pixels, area = count_red_area(image_path)
    print(f"Red pixel count: {pixels}")
    print(f"Estimated red area: {area:.4f} sq km")


