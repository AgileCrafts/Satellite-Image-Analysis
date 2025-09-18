import os
from datetime import datetime
from sqlalchemy.orm import Session
from models import SavedImage  
from database import SessionLocal,get_db
def save_images_from_folder(folder_path: str, db: Session):
    """
    Save images from a folder into the database.
    The filename is expected to contain a date in 'YYYY-MM-DD' format.
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' not found!")
        return

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(folder_path, filename)

            # Extract date from the filename (expects 'YYYY-MM-DD' format)
            try:
                date_str = os.path.splitext(filename)[0]
                image_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Skipping {filename}: filename not in valid 'YYYY-MM-DD' format")
                continue

            # Read the image file and convert it to binary data
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            # Create and add the Image record to the DB
            new_image = SavedImage(
                image=image_data,  # Store binary image data
                date=image_date,  # Store date parsed from filename
            )
            db.add(new_image)
            db.commit()
            db.refresh(new_image)

            print(f"Saved image '{filename}' (ID: {new_image.id}) with Date: {image_date}")

if __name__ == "__main__":
    db = SessionLocal()
    folder_path = 'images/'  # Change to the folder path where your images are stored
    save_images_from_folder(folder_path, db)
