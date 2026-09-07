import ee
import pandas as pd
import os
import sys

# ============================================================
# INITIALIZATION
# ============================================================
ee.Initialize(project="hackathon2026-507812")

FEATURES_FILE = r"data\sentinel1\croma_features_768.csv"
SCENES_FILE = r"data\sentinel1\selected_scenes_2024.csv"
OUTPUT_FILE = r"data\training_data.csv"

print("=" * 70)
print("MATCHING PATCHES WITH SEA-ICE CONCENTRATION (SIC) LABELS")
print("=" * 70)

# 1. Load Data with Error Handling
try:
    df_features = pd.read_csv(FEATURES_FILE)
    df_scenes = pd.read_csv(SCENES_FILE)
except FileNotFoundError as e:
    sys.exit(f"[CRITICAL ERROR] Could not find input files. Did the previous steps finish?\n{e}")

# 2. Merge Data and Check for Data Loss
df = pd.merge(df_features, df_scenes[["scene_id", "date"]], on="scene_id")

if len(df) != len(df_features):
    print(f"[WARNING] Row count mismatch! Features: {len(df_features)}, Merged: {len(df)}")
    print("Some scene_ids in the features file did not match the scenes file.")

CENTER_LON = -45.0
CENTER_LAT = -67.5
point = ee.Geometry.Point([CENTER_LON, CENTER_LAT])

labels = []
error_count = 0
zero_count = 0

# ============================================================
# FETCH LABELS VIA NOAA DAILY OISST
# ============================================================
print("Fetching NOAA OISST daily sea ice concentration...")

for idx, row in df.iterrows():
    date_str = str(row["date"]).split(" ")[0]
    
    try:
        collection = (
            ee.ImageCollection("NOAA/CDR/OISST/V2_1")
            .filterDate(date_str, ee.Date(date_str).advance(1, 'day'))
            .select("ice")
        )
        
        img = collection.first()
        
        if img is not None:
            result = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=25000 
            ).getInfo()
            
            sic = result.get("ice")
            sic_value = float(sic) if sic is not None else 0.0
        else:
            print(f"[!] No image found in dataset for {date_str}.")
            sic_value = 0.0
            error_count += 1
            
    except Exception as e:
        print(f"[!] API Error on {date_str}: {e}")
        sic_value = 0.0
        error_count += 1
        
    if sic_value == 0.0:
        zero_count += 1
        
    labels.append(sic_value)
    
    # Print progress every 25 patches
    if (idx + 1) % 25 == 0 or (idx + 1) == len(df):
        print(f"Processed [{idx + 1}/{len(df)}] labels (Latest SIC: {sic_value:.2f})")

# ============================================================
# FINALIZE DATASET
# ============================================================
df["sea_ice_concentration"] = labels

cols = ["scene_id", "date", "sea_ice_concentration"] + [c for c in df.columns if c.startswith("feat_")]
df = df[cols]

df.to_csv(OUTPUT_FILE, index=False)

# ============================================================
# DIAGNOSTIC REPORT
# ============================================================
print("\n" + "=" * 70)
print("EXECUTION DIAGNOSTICS & SUMMARY")
print("=" * 70)

print(f"Total rows processed : {len(df)}")
print(f"Total columns saved  : {df.shape[1]} (Expected: 771)")
print(f"API Errors / Missing : {error_count}")
print(f"Zero values (0.0)    : {zero_count}")

if error_count > 0:
    print("\n[WARNING] There were errors fetching some dates. Check the logs above.")
elif zero_count == len(df):
    print("\n[CRITICAL WARNING] All fetched values are 0.0. The NOAA dataset might not cover this exact coordinate, or the API is failing silently.")
elif len(df) < 200:
    print("\n[WARNING] You have less than 200 rows. Some patches were skipped or lost during extraction.")
else:
    print("\n[SUCCESS] Script executed perfectly with valid data variations!")

print(f"\nSaved final training dataset to: {OUTPUT_FILE}")
print("=" * 70)