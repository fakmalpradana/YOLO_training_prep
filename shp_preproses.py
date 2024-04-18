import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, Polygon
import os

# Input paths
shapefile_path = 'shp/Kav2.shp'
raster_folder = 'tile'
output_folder = 'shp_tile'

# Read the vector shapefile
gdf = gpd.read_file(shapefile_path)

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through all raster files in the folder
for filename in os.listdir(raster_folder):
    if filename.endswith('.tif'):
        raster_path = os.path.join(raster_folder, filename)
        output_shapefile_path = os.path.join(output_folder, filename[:-4] + '_clipped.shp')  # Create output shapefile path
        
        # Open the raster file
        with rasterio.open(raster_path) as src:
            # Get the extent of the raster
            raster_extent = src.bounds
            
            # Create a rectangular polygon from the raster extent
            raster_polygon = box(*raster_extent)
        
        # Clip the shapefile with the rectangular polygon
        clipped_gdf = gdf.intersection(raster_polygon)
        
        # Ensure the clipped geometries are converted to polygons
        clipped_gdf = clipped_gdf[clipped_gdf.geometry.type == 'Polygon']
        
        # Save the clipped shapefile
        clipped_gdf.to_file(output_shapefile_path)
        
        print(f"Clipped shapefile saved to: {output_shapefile_path}")
