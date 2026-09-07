import ee
import pandas as pd
import os

# ============================================================
# INITIALIZE EARTH ENGINE
# ============================================================

ee.Initialize(project="hackathon2026-507812")

print("=" * 70)
print("SENTINEL-1 SCENE SELECTION")
print("=" * 70)

TOTAL_TO_SELECT = 200
OUTPUT_FILE = r"data\sentinel1\selected_scenes_2024.csv"

# ============================================================
# WEDDELL SEA REGION
# ============================================================

aoi = ee.Geometry.Rectangle([
    -50, -70,
    -40, -65
])

# ============================================================
# SEARCH SENTINEL-1
# ============================================================

print()
print("Searching Sentinel-1...")

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(aoi)
    .filterDate("2024-01-01", "2025-01-01")
    .filter(ee.Filter.eq("instrumentMode", "EW"))
    .filter(
        ee.Filter.listContains(
            "transmitterReceiverPolarisation",
            "HH"
        )
    )
    .sort("system:time_start")
)

count = collection.size().getInfo()

print("Sentinel-1 scenes found:", count)

if count == 0:
    raise RuntimeError("No Sentinel-1 scenes found.")

# ============================================================
# FETCH ALL METADATA AT ONCE
# ============================================================

print()
print("Fetching all scene metadata in one request...")

metadata = collection.map(
    lambda image: ee.Feature(
        None,
        {
            "scene_id": image.get("system:index"),
            "time": image.get("system:time_start"),
            "orbit_pass": image.get("orbitProperties_pass"),
            "relative_orbit": image.get("relativeOrbitNumber_start")
        }
    )
)

# ONE REQUEST instead of 697 requests
features = metadata.getInfo()["features"]

print("Metadata received:", len(features))

# ============================================================
# CONVERT TO DATAFRAME
# ============================================================

records = []

for feature in features:
    p = feature["properties"]

    records.append({
        "scene_id": p.get("scene_id"),
        "date": pd.to_datetime(p.get("time"), unit="ms"),
        "orbit_pass": p.get("orbit_pass"),
        "relative_orbit": p.get("relative_orbit")
    })

df = pd.DataFrame(records)
df = df.sort_values("date").reset_index(drop=True)

print("Total scenes loaded:", len(df))

# ============================================================
# SELECT 200 SCENES EVENLY ACROSS 2024
# ============================================================

print()
print("Selecting approximately 200 scenes across 2024...")

selected_parts = []

base = TOTAL_TO_SELECT // 12
remainder = TOTAL_TO_SELECT % 12

for month in range(1, 13):

    monthly = df[df["date"].dt.month == month].copy()

    if len(monthly) == 0:
        print(f"Month {month:02d}: 0 available")
        continue

    target = base + (1 if month <= remainder else 0)
    target = min(target, len(monthly))

    # Evenly spaced positions
    if target == 1:
        positions = [len(monthly) // 2]
    else:
        positions = [
            round(i * (len(monthly) - 1) / (target - 1))
            for i in range(target)
        ]

    chosen = monthly.iloc[positions]

    selected_parts.append(chosen)

    print(
        f"Month {month:02d}: "
        f"{len(monthly)} available -> "
        f"{len(chosen)} selected"
    )

# ============================================================
# COMBINE AND SAVE
# ============================================================

selected_df = pd.concat(selected_parts, ignore_index=True)

selected_df = (
    selected_df
    .drop_duplicates(subset="scene_id")
    .sort_values("date")
    .reset_index(drop=True)
)

os.makedirs(r"data\sentinel1", exist_ok=True)

selected_df.to_csv(OUTPUT_FILE, index=False)

# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print("SELECTION COMPLETE")
print("=" * 70)

print("Available scenes:", len(df))
print("Selected scenes:", len(selected_df))
print("Date range:", selected_df["date"].min(), "to", selected_df["date"].max())

print()
print("Saved to:")
print(OUTPUT_FILE)

print()
print("First 10:")
print(selected_df.head(10).to_string(index=False))

print()
print("=" * 70)
print("DONE")
print("=" * 70)