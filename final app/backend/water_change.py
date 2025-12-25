# FINAL_PERFECT_WATER_CHANGE.py (Updated Robust Version)
import io
import numpy as np
import rioxarray
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, remove_small_holes
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union, transform
from shapely.affinity import translate, scale
import pyproj
import json
from PIL import Image
import matplotlib.pyplot as plt

import os

import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import transform_geom
from rasterio import features
from shapely.ops import unary_union

os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()


# ---------------- SCALING FUNCTIONS ----------------
def apply_scale_to_geometry(geometry, lat_scale=1.0, lon_scale=1.0):
    """
    Scale a geometry from its center point.
    
    Args:
        geometry: Shapely geometry object
        lat_scale: Scale factor for latitude (Y axis). >1 = expand, <1 = shrink
        lon_scale: Scale factor for longitude (X axis). >1 = expand, <1 = shrink
    
    Returns:
        Scaled geometry
    
    Examples:
        lat_scale=1.1 → 10% larger in north-south direction
        lon_scale=0.95 → 5% smaller in east-west direction
    """
    if geometry is None or geometry.is_empty:
        return geometry
    
    # Scale from the centroid of the geometry
    centroid = geometry.centroid
    return scale(geometry, xfact=lon_scale, yfact=lat_scale, origin=centroid)


# ---------------- OFFSET/SHIFT FUNCTIONS ----------------
def calculate_offset_from_percentage(geometry, lat_offset_percent=0, lon_offset_percent=0):
    """
    Calculate the actual lat/lon offset based on percentage of the geometry's bounding box.
    
    Args:
        geometry: Shapely geometry object
        lat_offset_percent: Percentage offset in latitude direction (-100 to 100)
        lon_offset_percent: Percentage offset in longitude direction (-100 to 100)
    
    Returns:
        Tuple of (lon_offset, lat_offset) in degrees
    """
    if geometry is None or geometry.is_empty:
        return 0.0, 0.0
    
    minx, miny, maxx, maxy = geometry.bounds
    width = maxx - minx   # longitude span
    height = maxy - miny  # latitude span
    
    # Calculate offset in degrees based on percentage
    lon_offset = (lon_offset_percent / 100.0) * width
    lat_offset = (lat_offset_percent / 100.0) * height
    
    return lon_offset, lat_offset


def apply_offset_to_geometry(geometry, lon_offset=0.0, lat_offset=0.0):
    """
    Apply coordinate offset to a Shapely geometry.
    
    Args:
        geometry: Shapely geometry object
        lon_offset: Offset in longitude (degrees) - positive moves east
        lat_offset: Offset in latitude (degrees) - positive moves north
    
    Returns:
        Translated geometry
    """
    if geometry is None or geometry.is_empty:
        return geometry
    
    # Use Shapely's translate function (xoff=longitude, yoff=latitude)
    return translate(geometry, xoff=lon_offset, yoff=lat_offset)


def apply_offset_to_geojson(geojson, lon_offset=0.0, lat_offset=0.0, 
                             lat_offset_percent=None, lon_offset_percent=None):
    """
    Apply coordinate offset to GeoJSON features.
    
    Args:
        geojson: GeoJSON dict with features
        lon_offset: Direct offset in longitude (degrees)
        lat_offset: Direct offset in latitude (degrees)
        lat_offset_percent: Percentage offset for latitude (overrides lat_offset if provided)
        lon_offset_percent: Percentage offset for longitude (overrides lon_offset if provided)
    
    Returns:
        New GeoJSON with offset coordinates
    """
    if not geojson or "features" not in geojson or len(geojson["features"]) == 0:
        return geojson
    
    new_features = []
    
    for feature in geojson["features"]:
        if "geometry" not in feature or feature["geometry"] is None:
            new_features.append(feature)
            continue
        
        geom = shape(feature["geometry"])
        
        # Calculate offset from percentage if provided
        if lat_offset_percent is not None or lon_offset_percent is not None:
            calc_lon_offset, calc_lat_offset = calculate_offset_from_percentage(
                geom,
                lat_offset_percent=lat_offset_percent or 0,
                lon_offset_percent=lon_offset_percent or 0
            )
            final_lon_offset = calc_lon_offset
            final_lat_offset = calc_lat_offset
        else:
            final_lon_offset = lon_offset
            final_lat_offset = lat_offset
        
        # Apply offset
        shifted_geom = apply_offset_to_geometry(geom, final_lon_offset, final_lat_offset)
        
        # Create new feature with shifted geometry
        new_feature = {
            "type": "Feature",
            "geometry": mapping(shifted_geom),
            "properties": {
                **feature.get("properties", {}),
                "offset_applied": {
                    "lon_offset_deg": final_lon_offset,
                    "lat_offset_deg": final_lat_offset,
                    "lat_offset_percent": lat_offset_percent,
                    "lon_offset_percent": lon_offset_percent
                }
            }
        }
        new_features.append(new_feature)
    
    return {
        "type": "FeatureCollection",
        "features": new_features
    }



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
def analyze_water_change(pre_bytes, post_bytes, output_dir="./", 
                          lat_offset_percent=0, lon_offset_percent=0,
                          lat_offset=0.0, lon_offset=0.0,
                          lat_scale=1.0, lon_scale=1.0):
    
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

        # Initialize tracking variables
        applied_lat_offset = 0.0
        applied_lon_offset = 0.0
        applied_lat_scale = lat_scale
        applied_lon_scale = lon_scale

        # STEP 1: Apply SCALING first (to fix size/ratio issues)
        # If one side aligns but other doesn't, adjust scale
        if lat_scale != 1.0 or lon_scale != 1.0:
            merged = apply_scale_to_geometry(merged, lat_scale=lat_scale, lon_scale=lon_scale)
            print(f"Applied scaling: lat_scale={lat_scale}, lon_scale={lon_scale}")

        # STEP 2: Apply OFFSET (to shift position)
        # Use percentage-based offset if provided, otherwise use direct offset
        if lat_offset_percent != 0 or lon_offset_percent != 0:
            calc_lon_offset, calc_lat_offset = calculate_offset_from_percentage(
                merged,
                lat_offset_percent=lat_offset_percent,
                lon_offset_percent=lon_offset_percent
            )
            merged = apply_offset_to_geometry(merged, calc_lon_offset, calc_lat_offset)
            applied_lat_offset = calc_lat_offset
            applied_lon_offset = calc_lon_offset
            print(f"Applied percentage offset: lat={lat_offset_percent}%, lon={lon_offset_percent}%")
            print(f"   → Actual offset: lat={calc_lat_offset:.6f}°, lon={calc_lon_offset:.6f}°")
        elif lat_offset != 0 or lon_offset != 0:
            merged = apply_offset_to_geometry(merged, lon_offset, lat_offset)
            applied_lat_offset = lat_offset
            applied_lon_offset = lon_offset
            print(f"Applied direct offset: lat={lat_offset:.6f}°, lon={lon_offset:.6f}°")

        merged_geojson = mapping(merged)


        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": merged_geojson,
                "properties": {
                    "change": "lost_water",
                    "transform_applied": {
                        "lat_offset_percent": lat_offset_percent,
                        "lon_offset_percent": lon_offset_percent,
                        "lat_offset_deg": applied_lat_offset,
                        "lon_offset_deg": applied_lon_offset,
                        "lat_scale": applied_lat_scale,
                        "lon_scale": applied_lon_scale
                    }
                }
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