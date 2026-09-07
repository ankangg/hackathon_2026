import rasterio
import numpy as np
import torch

INPUT_FILE = "data/sentinel1/sentinel1_hh_angle_real_patch_20240101.tif"
OUTPUT_FILE = "data/sentinel1/croma_input.npy"

print("=" * 60)
print("PREPARING REAL SENTINEL-1 DATA FOR CROMA")
print("=" * 60)

# ---------------------------------------------------------
# 1. Read Sentinel-1 TIFF
# ---------------------------------------------------------

with rasterio.open(INPUT_FILE) as src:
    data = src.read().astype(np.float32)

print("Original shape:", data.shape)

hh = data[0]
angle = data[1]

# ---------------------------------------------------------
# 2. Remove invalid HH pixels
# ---------------------------------------------------------

invalid = (hh == 0) | ~np.isfinite(hh)

print("Invalid HH pixels:", np.sum(invalid))

# Replace invalid pixels with median HH
valid_hh = hh[~invalid]
median_hh = np.median(valid_hh)

hh[invalid] = median_hh

# ---------------------------------------------------------
# 3. Normalize each channel
# ---------------------------------------------------------
# Robust normalization using mean ± 2 standard deviations

def normalize_channel(x):
    mean = np.mean(x)
    std = np.std(x)

    lower = mean - 2 * std
    upper = mean + 2 * std

    x = np.clip(x, lower, upper)

    x = (x - lower) / (upper - lower)

    return x


hh_norm = normalize_channel(hh)
angle_norm = normalize_channel(angle)

print()
print("HH normalized:")
print(" min:", hh_norm.min())
print(" max:", hh_norm.max())
print(" mean:", hh_norm.mean())

print()
print("Angle normalized:")
print(" min:", angle_norm.min())
print(" max:", angle_norm.max())
print(" mean:", angle_norm.mean())

# ---------------------------------------------------------
# 4. Stack the two channels
# ---------------------------------------------------------

image = np.stack([
    hh_norm,
    angle_norm
], axis=0)

print()
print("Stacked shape:", image.shape)

# ---------------------------------------------------------
# 5. Center crop to 120 × 120
# ---------------------------------------------------------

_, height, width = image.shape

crop_size = 120

start_y = (height - crop_size) // 2
start_x = (width - crop_size) // 2

image = image[
    :,
    start_y:start_y + crop_size,
    start_x:start_x + crop_size
]

print("Cropped shape:", image.shape)

# ---------------------------------------------------------
# 6. Save
# ---------------------------------------------------------

np.save(OUTPUT_FILE, image)

print()
print("Saved:", OUTPUT_FILE)

# ---------------------------------------------------------
# 7. Create PyTorch tensor
# ---------------------------------------------------------

tensor = torch.from_numpy(image).unsqueeze(0)

print()
print("CROMA tensor shape:", tensor.shape)
print("Tensor dtype:", tensor.dtype)

print("=" * 60)
print("PREPROCESSING COMPLETE")
print("=" * 60)