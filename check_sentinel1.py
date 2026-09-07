import ee

ee.Initialize(project="hackathon2026-507812")

aoi = ee.Geometry.Rectangle([
    -60, -75,
    -30, -60
])

base = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(aoi)
    .filterDate("2024-01-01", "2025-01-01")
    .filter(
        ee.Filter.listContains(
            "transmitterReceiverPolarisation",
            "HH"
        )
    )
    .filter(
        ee.Filter.listContains(
            "transmitterReceiverPolarisation",
            "HV"
        )
    )
)

print("=" * 70)
print("HH + HV SENTINEL-1 SCENES")
print("=" * 70)

count = base.size().getInfo()

print("Total HH + HV scenes:", count)
print()

images = base.sort("system:time_start").toList(count)

for i in range(count):

    img = ee.Image(images.get(i))

    props = img.toDictionary([
        "system:index",
        "system:time_start",
        "instrumentMode",
        "orbitProperties_pass",
        "relativeOrbitNumber_start",
        "transmitterReceiverPolarisation"
    ]).getInfo()

    timestamp = props["system:time_start"]

    from datetime import datetime, timezone

    date = datetime.fromtimestamp(
        timestamp / 1000,
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    # Get footprint bounding box
    bounds = img.geometry().bounds()

    coords = bounds.coordinates().getInfo()[0]

    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]

    print("-" * 70)
    print("Scene", i + 1)
    print("ID:", props.get("system:index"))
    print("Date:", date)
    print("Mode:", props.get("instrumentMode"))
    print("Orbit:", props.get("orbitProperties_pass"))
    print("Relative orbit:", props.get("relativeOrbitNumber_start"))
    print("Polarization:",
          props.get("transmitterReceiverPolarisation"))

    print(
        "Longitude:",
        round(min(lons), 3),
        "to",
        round(max(lons), 3)
    )

    print(
        "Latitude:",
        round(min(lats), 3),
        "to",
        round(max(lats), 3)
    )

    print("Bands:", img.bandNames().getInfo())

print()
print("=" * 70)
print("COMPLETE")
print("=" * 70)