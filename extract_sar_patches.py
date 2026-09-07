import os
import urllib.request
import ee
import numpy as np
import pandas as pd

# ============================================================
# INITIALIZATION
# ============================================================
ee.Initialize(project="hackathon2026-507812")

CSV_FILE = r"data/sentinel1/selected_scenes_2024.csv"
OUTPUT_DIR = r"data/sentinel1/patches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_FILE)
print(f"Loaded {len(df)} selected scenes.")

# Patch parameters: CROMA expects 120x120 patches
PATCH_SIZE = 120
SCALE = 40  # 40m resolution per pixel (Sentinel-1 EW mode)

# Fixed study area center in the Weddell Sea
CENTER_LON = -45.0
CENTER_LAT = -67.5

point = ee.Geometry.Point([CENTER_LON, CENTER_LAT])
region = point.buffer((PATCH_SIZE * SCALE) / 2).bounds()

# ============================================================
# DOWNLOAD PATCHES DIRECTLY FROM EARTH ENGINE
# ============================================================
print("Extracting SAR patches directly via Earth Engine...")

success_count = 0

for idx, row in df.iterrows():
    scene_id = row["scene_id"]
    out_path = os.path.join(OUTPUT_DIR, f"{scene_id}_patch.npy")

    if os.path.exists(out_path):
        print(f"[{idx+1}/{len(df)}] Already exists: {scene_id}")
        success_count += 1
        continue

    try:
        img = ee.Image(f"COPERNICUS/S1_GRD/{scene_id}").select(["HH"])

        # Fetch patch as raw array without full-scene download
        url = img.getDownloadURL(
            {
                "region": region,
                "scale": SCALE,
                "format": "NPY",
            }
        )

        urllib.request.urlretrieve(url, out_path)
        print(f"[{idx+1}/{len(df)}] Saved: {scene_id}")
        success_count += 1

    except Exception as e:
        print(f"[{idx+1}/{len(df)}] Failed {scene_id}: {e}")

print("\n" + "=" * 70)
print(f"EXTRACTION COMPLETE: {success_count}/{len(df)} patches saved.")
print(f"Saved directory: {OUTPUT_DIR}")
print("=" * 70)