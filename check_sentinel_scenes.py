import ee

# ---------------------------------------------------------
# Earth Engine
# ---------------------------------------------------------

ee.Initialize(project="hackathon2026-507812")

print("=" * 70)
print("SENTINEL-1 SCENE INVENTORY")
print("=" * 70)

# ---------------------------------------------------------
# Target Weddell Sea region
# ---------------------------------------------------------

aoi = ee.Geometry.Rectangle([
    -50,   # west
    -70,   # south
    -40,   # east
    -65    # north
])

# ---------------------------------------------------------
# Sentinel-1 collection
# ---------------------------------------------------------

collection = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(aoi)
    .filterDate(
        "2024-01-01",
        "2025-01-01"
    )
    .filter(
        ee.Filter.eq(
            "instrumentMode",
            "EW"
        )
    )
    .filter(
        ee.Filter.listContains(
            "transmitterReceiverPolarisation",
            "HH"
        )
    )
)

count = collection.size().getInfo()

print()
print("Usable HH/EW scenes:", count)

# ---------------------------------------------------------
# Get metadata
# ---------------------------------------------------------

scenes = collection.sort(
    "system:time_start"
).toList(count)

print()
print("SCENES:")
print("-" * 70)

for i in range(count):

    image = ee.Image(scenes.get(i))

    info = image.toDictionary([
        "system:index",
        "system:time_start",
        "orbitProperties_pass",
        "relativeOrbitNumber_start",
        "resolution_meters",
        "transmitterReceiverPolarisation"
    ]).getInfo()

    date = ee.Date(
        info["system:time_start"]
    ).format(
        "YYYY-MM-dd HH:mm"
    ).getInfo()

    print(
        f"{i+1:3d}. "
        f"{date} | "
        f"{info.get('orbitProperties_pass')} | "
        f"Orbit {info.get('relativeOrbitNumber_start')} | "
        f"{info.get('system:index')}"
    )

print()
print("=" * 70)
print("INVENTORY COMPLETE")
print("=" * 70)