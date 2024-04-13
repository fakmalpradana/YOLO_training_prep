import os
from PIL import Image

def convert_tif_to_png(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all files in the input folder
    files = os.listdir(input_folder)

    # Loop through each file in the input folder
    for file in files:
        # Check if the file is a tif file
        if file.lower().endswith('.tif'):
            # Open the tif image
            with Image.open(os.path.join(input_folder, file)) as img:
                # Construct the output file path
                output_file = os.path.join(output_folder, os.path.splitext(file)[0] + '.png')
                # Convert and save the image as png
                img.save(output_file, 'PNG')
                print(f"Converted {file} to PNG")

# Replace 'input_folder' and 'output_folder' with your actual folder paths
input_folder = 'tile'
output_folder = 'tile_png'

convert_tif_to_png(input_folder, output_folder)
