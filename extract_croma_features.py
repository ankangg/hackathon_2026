import os
import sys
import glob
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

# Point Python to the nested CROMA directory based on your previous logs
sys.path.append(os.path.join("croma", "CROMA"))
sys.path.append("croma")

try:
    from use_croma import PretrainedCROMA
except ModuleNotFoundError:
    raise RuntimeError("Could not find 'use_croma.py'. Make sure the CROMA GitHub repo is cloned into your 'croma' folder.")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Dynamically locate the weights file depending on where curl saved it
WEIGHTS_PATH = os.path.join("croma", "CROMA_base.pt")
if not os.path.exists(WEIGHTS_PATH):
    WEIGHTS_PATH = os.path.join("croma", "CROMA", "CROMA_base.pt")

PATCHES_DIR = os.path.join("data", "sentinel1", "patches")
OUTPUT_FILE = os.path.join("data", "sentinel1", "croma_features_768.csv")

# 1. Load Pretrained CROMA model
print(f"Loading CROMA model onto {DEVICE} from {WEIGHTS_PATH}...")
model = PretrainedCROMA(
    pretrained_path=WEIGHTS_PATH,
    size="base",
    modality="SAR",
    image_resolution=120
).to(DEVICE)
model.eval()

# 2. Collect extracted patch files
patch_files = glob.glob(os.path.join(PATCHES_DIR, "*_patch.npy"))
print(f"Found {len(patch_files)} patches to process.")

records = []

with torch.no_grad():
    for idx, file_path in enumerate(patch_files):
        scene_id = os.path.basename(file_path).replace("_patch.npy", "")
        
        try:
            arr = np.load(file_path)
            
            # Handle structured or multi-dimensional GEE NPY outputs
            if arr.dtype.names:
                arr = arr[arr.dtype.names[0]]
            
            arr = np.squeeze(arr).astype(np.float32)
            
            # Interpolate or pad to exactly (120, 120) if needed
            tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
            if tensor.shape[-2:] != (120, 120):
                tensor = F.interpolate(tensor, size=(120, 120), mode="bilinear", align_corners=False)
            
            # CROMA expects 2 channels for SAR (e.g., HH/HV); duplicate single-polarization HH to 2 channels
            sar_input = tensor.repeat(1, 2, 1, 1).to(DEVICE)
            
            # Normalize inputs
            mean = sar_input.mean(dim=(-2, -1), keepdim=True)
            std = sar_input.std(dim=(-2, -1), keepdim=True) + 1e-6
            sar_input = (sar_input - mean) / std

            # Extract representations
            outputs = model(SAR_images=sar_input)
            
            # SAR_GAP gives the 768-dim pooled feature vector
            embedding = outputs["SAR_GAP"].squeeze(0).cpu().numpy()
            
            row = {"scene_id": scene_id}
            for i, val in enumerate(embedding):
                row[f"feat_{i}"] = val
            records.append(row)

            if (idx + 1) % 25 == 0 or (idx + 1) == len(patch_files):
                print(f"Processed [{idx + 1}/{len(patch_files)}] patches")

        except Exception as e:
            print(f"Error processing {scene_id}: {e}")

# 3. Save feature matrix
df_features = pd.DataFrame(records)
df_features.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 70)
print(f"Successfully extracted {df_features.shape[1] - 1} features for {len(df_features)} scenes.")
print(f"Saved features to: {OUTPUT_FILE}")
print("=" * 70)