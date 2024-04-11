import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping, Polygon, MultiPolygon
from tqdm.auto import tqdm
from time import sleep
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
        if row["geometry"] is None:
            # Skip rows with empty geometries
            continue
        
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

    # LIST_IMG = glob('public/patch-temp/patch*.png')
    # with tqdm(total=len(LIST_IMG), desc='Proses deteksi bangunan', leave=True) as pbar:
    #     for i in LIST_IMG:
    #         a = Predict(img=i, model=MODEL).to_json(i.replace('png','json'), TIPE)
    #         pbar.update(1)

    with tqdm(total=len(raster_files), desc='Proses konversi', position=0, leave=True,) as pbar:
        for i in raster_files:
            raster_path = os.path.join(raster_folder, i)
            shapefile_path = os.path.join(shapefile_folder, os.path.splitext(i)[0] + '_clipped.shp')

            # Read the raster file to extract extent, width, and height
            with rasterio.open(raster_path) as src:
                extent = src.bounds
                width = src.width
                height = src.height

            # Convert shapefile to COCO JSON
            output_json_path = os.path.join(coco_output_folder, os.path.splitext(i)[0] + '_coco.json')
            shp_to_coco(shapefile_path, i, extent, width, height, output_json_path)

            pbar.update(1)
            sleep(0.01)
            

print("Batch processing completed!")
