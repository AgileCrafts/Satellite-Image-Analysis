import os
from PIL import Image, ImageDraw, ImageFont

# Folder where images are stored
image_folder = 'rgb_images/'

# Get all image files in the folder (e.g., .png, .jpg)
image_files = [f for f in os.listdir(image_folder) if f.endswith(('png', 'jpg', 'jpeg'))]

# Sort the images by filename (optional, depending on your naming convention)
image_files.sort()
    # Choose a font (default system font or specify path to a font file)
font_size=100
font = ImageFont.load_default()

# Open the images and store them in a list
images = []
for file in image_files:
    img_path = os.path.join(image_folder, file)
    image = Image.open(img_path)

    # Draw the filename on the image
    draw = ImageDraw.Draw(image)


    # Set the position and text color
    text_position = (10, 10)  # Top-left corner
    text_color = (255, 255, 255)  # White text color

    # Add the filename to the image
    draw.text(text_position, file, font=font, fill=text_color)

    # Append the image to the list
    images.append(image)

# Save as GIF (using the first image and appending the rest)
images[0].save('output.gif', save_all=True, append_images=images[1:], duration=500, loop=0)

