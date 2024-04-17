import os
import json

def coco_to_yolov8_segmentation(coco_json_path, output_txt_path, class_mapping):
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)

    annotations = coco_data['annotations']
    images = coco_data['images']
    categories = coco_data.get('categories', [])

    # Create a dictionary to map category IDs to YOLO class IDs
    class_id_mapping = {category['id']: class_id for class_id, category in enumerate(categories)}

    with open(output_txt_path, 'w') as out_file:
        for annotation in annotations:
            image_id = annotation['image_id']

            # Check if the image_id is valid
            if not any(image['id'] == image_id for image in images):
                print(f"Warning: Image with ID {image_id} not found in 'images' list. Skipping.")
                continue

            category_id = annotation['category_id']
            segmentation = annotation['segmentation'][0]  # Take the first segmentation (assuming only one per instance)

            # Map COCO category ID to YOLO class ID
            yolo_class_id = class_id_mapping.get(category_id)

            # Check if the category_id is valid
            if yolo_class_id is None:
                print(f"Warning: Category with ID {category_id} not found in class mapping. Skipping.")
                continue

            # Convert segmentation to YOLOv8 format
            segment_line = f"{yolo_class_id} "
            for i in range(0, len(segmentation), 2):
                x, y = segmentation[i], segmentation[i + 1]
                x_norm = x / images[image_id - 1]['width']
                y_norm = y / images[image_id - 1]['height']
                segment_line += f"{x_norm} {y_norm} "

            # Write YOLOv8 format to the output file
            out_file.write(segment_line.strip() + "\n")

def process_folder(input_folder, output_folder):
    # Ensure output folder exists, create it if it doesn't
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Define the mapping of COCO class IDs to YOLOv8 class IDs
    class_mapping = {
        1: 0,  # Map COCO class ID 1 to YOLOv8 class ID 0
    }

    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_file_path = os.path.join(input_folder, filename)
            name = filename.split('.')[0]
            output_file_path = os.path.join(output_folder, name.replace('_coco', '') + '.txt')

            coco_to_yolov8_segmentation(input_file_path, output_file_path, class_mapping)

if __name__ == "__main__":
    input_folder = "coco"
    output_folder = "yolo_txt"

    process_folder(input_folder, output_folder)
