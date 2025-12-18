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


# from PIL import Image
# import numpy as np

# from PIL import Image

# # Open the TIFF image
# image = Image.open("lost_water_mask.tif")
# image.show()

# import rasterio

# # Open the GeoTIFF file
# with rasterio.open('lost_water_mask.tif') as dataset:
#     # Get the CRS (Coordinate Reference System)
#     crs = dataset.crs
#     print(f"CRS: {crs}")

import os
import pyproj
import rasterio

# Force correct PROJ path (pyproj bundled PROJ)
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

# Force correct GDAL path (Rasterio internal)
# os.environ["GDAL_DATA"] = rasterio._gdal_data