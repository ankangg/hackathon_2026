import ee
import os

ee.Initialize(project="hackathon2026-507812")

SCENE_ID = (
    "S1A_EW_GRDM_1SSH_20240101T230241_"
    "20240101T230346_051919_0645DF_43BB"
)

OUTPUT_DIR = "data/sentinel1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("SENTINEL-1 REAL SAR PATCH DOWNLOAD")
print("=" * 60)

# ------------------------------------------------------------
# GET SCENE
# ------------------------------------------------------------

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filter(
        ee.Filter.eq("system:index", SCENE_ID)
    )
)

if collection.size().getInfo() == 0:
    raise RuntimeError("Scene not found.")

image = ee.Image(collection.first())

print("Scene found:", SCENE_ID)
print("Bands:", image.bandNames().getInfo())

# ------------------------------------------------------------
# VALID POINT INSIDE THE ACTUAL SCENE
# ------------------------------------------------------------

center_lon = -48.21487436630489
center_lat = -64.61692840504057

center = ee.Geometry.Point([
    center_lon,
    center_lat
])

# ------------------------------------------------------------
# CREATE SMALL PATCH
# ------------------------------------------------------------
# 120 x 120 pixels at approximately 40 m
# ~4.8 km x 4.8 km
# ------------------------------------------------------------

patch = center.buffer(2400).bounds()

# ------------------------------------------------------------
# SELECT REAL SAR BANDS
# ------------------------------------------------------------

selected = image.select([
    "HH",
    "angle"
]).clip(patch)

# ------------------------------------------------------------
# VERIFY VALUES BEFORE DOWNLOAD
# ------------------------------------------------------------

print()
print("Checking HH values...")

stats = selected.reduceRegion(
    reducer=ee.Reducer.mean()
        .combine(
            ee.Reducer.minMax(),
            sharedInputs=True
        ),
    geometry=patch,
    scale=40,
    maxPixels=100000
).getInfo()

print("Statistics:", stats)

# ------------------------------------------------------------
# DOWNLOAD
# ------------------------------------------------------------

print()
print("Creating download URL...")

url = selected.getDownloadURL({
    "name": "sentinel1_hh_angle_real_patch_20240101",
    "region": patch,
    "scale": 40,
    "crs": "EPSG:4326",
    "filePerBand": False,
    "format": "GEO_TIFF"
})

print()
print("=" * 60)
print("DOWNLOAD URL")
print("=" * 60)
print(url)

print()
print("Save the downloaded file as:")
print(
    "data/sentinel1/"
    "sentinel1_hh_angle_real_patch_20240101.tif"
)

print("=" * 60)