# FINAL_PERFECT_WATER_CHANGE.py (Updated Robust Version)
import io
import numpy as np
import rioxarray
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
import pyproj
import json
from PIL import Image
import matplotlib.pyplot as plt

import os
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()

import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import transform_geom
from rasterio import features
from shapely.ops import unary_union

# ---------------- LOAD 5-BAND GEOTIFF ----------------
def load_s2_tiff_riox(tiff_bytes):
    xds = rioxarray.open_rasterio(io.BytesIO(tiff_bytes))

    # ---------------- FIX: Reproject to EPSG:4326 ----------------
    if xds.rio.crs.to_string() != "EPSG:4326":
        xds = xds.rio.reproject("EPSG:4326")

    green = xds.isel(band=0).values.astype(np.float32)   # B03: Green
    swir1 = xds.isel(band=3).values.astype(np.float32)   # B11: SWIR1

    transform = xds.rio.transform()  # now in lon/lat
    crs = xds.rio.crs                 # EPSG:4326
    bounds = xds.rio.bounds()
    
    
    for i in range(len(xds.band)):
        band = xds.isel(band=i).values
        print(f"Band {i} min/max: {band.min()}/{band.max()}")

    xds.close()
    return green, swir1, transform, crs, bounds


# ---------------- MNDWI & MASK ----------------
def calculate_mndwi(green_band, swir1_band):
    denominator = green_band + swir1_band
    return np.where(denominator == 0, 0, (green_band - swir1_band) / denominator)

def create_water_mask(mndwi_image, threshold):
    return mndwi_image > threshold



# ---------------- FULL CHANGE MAP + GEOJSON + GEOTIFF ----------------
def analyze_water_change(pre_bytes, post_bytes, output_dir="./"):
    
    # Load both images
    pre_green, pre_swir1, pre_transform, pre_crs, pre_bounds = load_s2_tiff_riox(pre_bytes)
    post_green, post_swir1, post_transform, post_crs, post_bounds = load_s2_tiff_riox(post_bytes)

    pre_mndwi = calculate_mndwi(pre_green, pre_swir1)
    post_mndwi = calculate_mndwi(post_green, post_swir1)
    
    pre_thresh = threshold_otsu(pre_mndwi)
    post_thresh = threshold_otsu(post_mndwi)

    pre_mask = remove_small_objects(remove_small_holes(create_water_mask(pre_mndwi, pre_thresh), area_threshold=8000), min_size=200)
    post_mask = remove_small_objects(remove_small_holes(create_water_mask(post_mndwi, post_thresh), area_threshold=8000), min_size=200)

    # Ensure same shape
    min_rows = min(pre_mask.shape[0], post_mask.shape[0])
    min_cols = min(pre_mask.shape[1], post_mask.shape[1])
    pre_mask = pre_mask[:min_rows, :min_cols]
    post_mask = post_mask[:min_rows, :min_cols]

    change_map_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    COLOR_PERSISTENT_WATER = [0, 0, 255]
    COLOR_NEW_WATER = [0, 255, 0]
    COLOR_LOST_WATER = [255, 0, 0]
    COLOR_NO_CHANGE_LAND = [128, 128, 128]

    pre_int = pre_mask.astype(np.uint8)
    post_int = post_mask.astype(np.uint8)

    # change_map_rgb[(pre_int==0) & (post_int==0)] = COLOR_NO_CHANGE_LAND
    # change_map_rgb[(pre_int==1) & (post_int==1)] = COLOR_PERSISTENT_WATER
    # change_map_rgb[(pre_int==0) & (post_int==1)] = COLOR_NEW_WATER
    # change_map_rgb[(pre_int==1) & (post_int==0)] = COLOR_LOST_WATER


    # Calculate pixel counts for each category
    persistent_count = np.sum((pre_int == 1) & (post_int == 1))
    new_count = np.sum((pre_int == 0) & (post_int == 1))
    lost_count = np.sum((pre_int == 1) & (post_int == 0))
    no_change_count = np.sum((pre_int == 0) & (post_int == 0))
    


    # Full change map (RGB)
    change_rgb = np.zeros((min_rows, min_cols, 3), dtype=np.uint8)
    change_rgb[(~pre_mask) & (~post_mask)] = [128, 128, 128]  # Land
    change_rgb[(pre_mask) & (post_mask)] = [0, 0, 255]      # Persistent water
    change_rgb[(~pre_mask) & (post_mask)] = [0, 255, 0]      # New water
    change_rgb[(pre_mask) & (~post_mask)] = [255, 0, 0]      # Lost water

    # Save change map PNG
    change_map_bytes = io.BytesIO()
    Image.fromarray(change_rgb).save(change_map_bytes, format="PNG")
    change_map_bytes = change_map_bytes.getvalue()
    

    # Lost water mask (binary)
    lost_water_mask = pre_mask & (~post_mask)

    # Save as GeoTIFF (perfect georeferencing!)
    lost_tif_path = f"{output_dir}/lost_water_mask.tif"
    
    
    
    profile = {
        'driver': 'GTiff',
        'height': min_rows,
        'width': min_cols,
        'count': 1,
        'dtype': 'uint8',
        'crs': pre_crs,
        'transform': pre_transform,
        'compress': 'deflate'
    }
    with rasterio.open(lost_tif_path, 'w', **profile) as dst:
        dst.write(lost_water_mask.astype(np.uint8) * 255, 1)
    print(f"GeoTIFF saved: {lost_tif_path}")

    # Extract polygons → GeoJSON (lon/lat)
    # polygons = []
    # for geom, val in rasterio.features.shapes(lost_water_mask.astype(np.uint8), transform=pre_transform):
    #     if val == 1:
    #         poly = shape(geom)
    #         if poly.is_valid and poly.area > 0:
    #             polygons.append(poly)

    # if polygons:
    #     merged = unary_union(polygons).simplify(0.00003, preserve_topology=True)
    #     if pre_crs and str(pre_crs) != "EPSG:4326":
    #         transformer = pyproj.Transformer.from_crs(pre_crs, "EPSG:4326", always_xy=True)
    #         merged = transform(transformer.transform, merged)
    #     geojson = {
    #         "type": "FeatureCollection",
    #         "features": [{
    #             "type": "Feature",
    #             "geometry": mapping(merged),
    #             "properties": {
    #                 "change": "lost_water",
    #                 "area_m2": merged.area,
    #                 "area_ha": round(merged.area / 10000, 2)
    #             }
    #         }]
    #     }
    
    # polygons = []
    # for geom, val in features.shapes(lost_water_mask.astype(np.uint8), transform=pre_transform):
    #     if val == 1:
    #         polygons.append(geom)

    # if polygons:
    #     # Convert to Shapely and merge
    #     shapely_polys = [shape(p) for p in polygons]
    #     merged = unary_union(shapely_polys)
    #     merged = merged.simplify(0.00001, preserve_topology=True)

    #     # Transform to WGS84 for Mapbox
    #     merged_geojson = transform_geom(str(pre_crs), "EPSG:4326", mapping(merged), precision=6)

    #     geojson = {
    #         "type": "FeatureCollection",
    #         "features": [{
    #             "type": "Feature",
    #             "geometry": merged_geojson,
    #             "properties": {"change": "lost_water"}
    #         }]
    #     }
    # else:
    #     geojson = {"type": "FeatureCollection", "features": []}

    # # Save to file
    # geojson_path = f"{output_dir}/lost_water.geojson"
    # with open(geojson_path, "w") as f:
    #     json.dump(geojson, f, indent=2)
    # print(f"GeoJSON saved: {geojson_path}")
    polygons = []

    # pre_transform MUST be the transform from the reprojected TIFF (EPSG:4326)
    for geom, val in features.shapes(
            lost_water_mask.astype(np.uint8),
            transform=pre_transform
    ):
        if val == 1:
            polygons.append(geom)   

    if polygons:
        # Convert to Shapely + merge
        shapely_polys = [shape(p) for p in polygons]
        merged = unary_union(shapely_polys)

        # Optional: very small simplify (degrees!)
        merged = merged.simplify(0.0001, preserve_topology=True)

        # 🚫 NO transform_geom anymore
        merged_geojson = mapping(merged)


        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": merged_geojson,
                "properties": {"change": "lost_water"}
            }]
        }
    else:
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

    # Save to file
    geojson_path = f"{output_dir}/lost_water.geojson"
    with open(geojson_path, "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"GeoJSON saved: {geojson_path}")
    
    
    # if port_id and db:
    #     try:
    #         port = db.query(Port).filter(Port.id == port_id).first()
    #         if port:
    #             port.geojson = geojson  # Store directly as JSON object (jsonb)
    #             db.commit()
    #             print(f"GeoJSON saved to Port ID: {port_id}")
    #         else:
    #             print(f"Port with ID {port_id} not found in DB.")
    #     except Exception as e:
    #         print(f"Error saving GeoJSON to DB: {e}")
    #         db.rollback()

    # Statistics
    lost_pixels = np.sum(lost_water_mask)
    area_m2 = lost_pixels * 100  # 10m x 10m
    lost_area_ha = area_m2 / 10000

    print(f"\nWater Change Summary:")
    print(f"   Lost water: {lost_pixels:,} pixels → {lost_area_ha:.2f} hectares")

    return {
        "change_map_png": change_map_bytes,
        "lost_water_tif": lost_tif_path,
        "lost_water_geojson": geojson_path,
        "lost_area_ha": lost_area_ha,
        "geojson": geojson
    }

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)

    pre_path  = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\tiff_images\NDWI_5band_2020-01-17.tif"
    post_path = r"D:\Satellite Image Analysis\Satellite-Image-Analysis\final app\backend\tiff_images\NDWI_5band_2024-12-01.tif"

    with open(pre_path, "rb") as f:
        pre_bytes = f.read()
    with open(post_path, "rb") as f:
        post_bytes = f.read()

    result = analyze_water_change(pre_bytes, post_bytes, output_dir="output")

    # Save change map PNG
    with open("output/change_map.png", "wb") as f:
        f.write(result["change_map_png"])

    print("\nAll done!")
    print("   change_map.png")
    print("   lost_water_mask.tif  ← perfect georeferenced")
    print("   lost_water.geojson   ← ready for map")
