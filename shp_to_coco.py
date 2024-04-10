# import geopandas as gpd
# import json
# from shapely.geometry import mapping, Polygon

# EXTENT = [
#     431444.7000000000116415,9138614.8499999996274710,
#     432923.2500000000000000,9139330.0500000007450581
# ]
# WIDTH, HEIGHT = 1479, 715

# def shift_to_origin(geometry):
    

#     min_x, min_y, max_x, max_y = EXTENT[0], EXTENT[1], EXTENT[2], EXTENT[3]
#     scale_x = (max_x - min_x)/(WIDTH)
#     scale_y = (max_y - min_y)/(HEIGHT)

#     # shifted_coordinates = [
#     #     ((x - min_x) / scale_x, (y - min_y) / scale_y) for x, y in geometry.exterior.coords
#     # ]
    
#     shifted_coordinates = [((x - min_x)/scale_x, HEIGHT - ((y - min_y)/scale_y)) for x, y in geometry.exterior.coords]
#     return Polygon(shifted_coordinates)


# def shp_to_coco(shp_path, image_filename, output_json):
#     # Read the shapefile
#     gdf = gpd.read_file(shp_path)

#     # Shift coordinates to start from (0, 0)
#     gdf["geometry"] = gdf["geometry"].apply(shift_to_origin)

#     # Create COCO annotation structure
#     coco_data = {
#         "info": {},
#         "licenses": [],
#         "images": [],
#         "annotations": [],
#         "categories": [{"id": 1, "name": "building", "supercategory": "building"}]
#     }

#     # Add image information
#     image_id = 1
#     image_data = {
#         "id": image_id,
#         "file_name": image_filename,
#         "width": WIDTH,  # replace with the actual width of your image
#         "height": HEIGHT,  # replace with the actual height of your image
#         "license": None,
#         "flickr_url": None,
#         "coco_url": None,
#         "date_captured": None
#     }
#     coco_data["images"].append(image_data)

#     # Add annotation information
#     for idx, row in gdf.iterrows():
#         polygon = mapping(row["geometry"])
        
#         seg = []
#         for i in polygon["coordinates"][0]:
#             for j in i:
#                 seg.append(j)

#         annotation_data = {
#             "id": idx + 1,
#             "image_id": image_id,
#             "category_id": 1,
#             "segmentation": [seg],
#             "area": row["geometry"].area,
#             "bbox": [row["geometry"].bounds[0], row["geometry"].bounds[1],
#                      row["geometry"].bounds[2] - row["geometry"].bounds[0],
#                      row["geometry"].bounds[3] - row["geometry"].bounds[1]],
#             "iscrowd": 0
#         }
#         coco_data["annotations"].append(annotation_data)

#     # Save COCO JSON file
#     with open(output_json, "w") as json_file:
#         json.dump(coco_data, json_file, indent=4)

#     print(f"COCO JSON file saved to: {output_json}")

# if __name__ == "__main__":
#     # Specify the path to your shapefile, image filename, and output JSON file
#     shapefile_path = "Progress/Campur DIY dan Kavling 1/digitasi_padat.shp"
#     image_filename = "Progress/padat-01-cropped1-15cm.png"
#     output_json_path = "Progress/padat-01-cropped1-15cm-v2.json"

#     # Convert shapefile to COCO JSON
#     shp_to_coco(shapefile_path, image_filename, output_json_path)


# Untuk Batch Process dibawah ini


import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping, Polygon, MultiPolygon
from tqdm import tqdm
import json

# Function to shift coordinates to origin
def shift_to_origin(geometry, extent, width, height):
    min_x, min_y, max_x, max_y = extent
    scale_x = (max_x - min_x) / width
    scale_y = (max_y - min_y) / height

    if isinstance(geometry, Polygon):
        shifted_coordinates = [
            ((x - min_x) / scale_x, height - ((y - min_y) / scale_y)) for x, y in geometry.exterior.coords
        ]
        return Polygon(shifted_coordinates)
    elif isinstance(geometry, MultiPolygon):
        shifted_polygons = []
        for polygon in geometry.geoms:
            shifted_coordinates = [
                ((x - min_x) / scale_x, height - ((y - min_y) / scale_y)) for x, y in polygon.exterior.coords
            ]
            shifted_polygons.append(Polygon(shifted_coordinates))
        return MultiPolygon(shifted_polygons)
    else:
        return geometry

# Function to convert shapefile to COCO JSON
def shp_to_coco(shp_path, image_filename, extent, width, height, output_json):
    # Read the shapefile
    gdf = gpd.read_file(shp_path)

    # Shift coordinates to start from (0, 0)
    gdf["geometry"] = gdf["geometry"].apply(shift_to_origin, extent=extent, width=width, height=height)

    # Create COCO annotation structure
    coco_data = {
        "info": {},
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": [{"id": 1, "name": "building", "supercategory": "building"}]
    }

    # Add image information
    image_id = 1
    image_data = {
        "id": image_id,
        "file_name": image_filename.replace('.tif', '.png'),  # Replace 'tif' with 'png'
        "width": width,
        "height": height,
        "license": None,
        "flickr_url": None,
        "coco_url": None,
        "date_captured": None
    }
    coco_data["images"].append(image_data)

    # Add annotation information
    for idx, row in gdf.iterrows():
        polygon = mapping(row["geometry"])

        seg = []
        for i in polygon["coordinates"][0]:
            for j in i:
                seg.append(j)

        annotation_data = {
            "id": idx + 1,
            "image_id": image_id,
            "category_id": 1,
            "segmentation": [seg],
            "area": row["geometry"].area,
            "bbox": [row["geometry"].bounds[0], row["geometry"].bounds[1],
                     row["geometry"].bounds[2] - row["geometry"].bounds[0],
                     row["geometry"].bounds[3] - row["geometry"].bounds[1]],
            "iscrowd": 0
        }
        coco_data["annotations"].append(annotation_data)

    # Save COCO JSON file
    with open(output_json, "w") as json_file:
        json.dump(coco_data, json_file, indent=4)

    print(f"COCO JSON file saved to: {output_json}")

if __name__ == "__main__":
    # Specify the paths to the raster and shapefile directories
    raster_folder = 'tile'
    shapefile_folder = 'shp_tile'
    coco_output_folder = 'coco'  # Updated output folder

    # Get a list of raster files in the raster folder
    raster_files = [file for file in os.listdir(raster_folder) if file.endswith('.tif')]

    # Iterate over raster files
    for raster_file in tqdm(raster_files, desc='Processing Rasters'):
        # Construct the paths for the current raster and corresponding shapefile
        raster_path = os.path.join(raster_folder, raster_file)
        shapefile_path = os.path.join(shapefile_folder, os.path.splitext(raster_file)[0] + '_clipped.shp')

        # Read the raster file to extract extent, width, and height
        with rasterio.open(raster_path) as src:
            extent = src.bounds
            width = src.width
            height = src.height

        # Convert shapefile to COCO JSON
        output_json_path = os.path.join(coco_output_folder, os.path.splitext(raster_file)[0] + '_coco.json')
        shp_to_coco(shapefile_path, raster_file, extent, width, height, output_json_path)

print("Batch processing completed!")
