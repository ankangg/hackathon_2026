import sys
import os
import numpy as np
import torch

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

CROMA_PATH = r"croma\CROMA"
WEIGHTS_FILE = r"croma\CROMA\CROMA_base.pt"

INPUT_FILE = r"data\sentinel1\croma_input.npy"
OUTPUT_FILE = r"data\sentinel1\croma_embedding_20240101.npy"

# ---------------------------------------------------------
# Add CROMA repository to Python path
# ---------------------------------------------------------

sys.path.append(CROMA_PATH)

from use_croma import PretrainedCROMA


print("=" * 60)
print("CROMA REAL SENTINEL-1 INFERENCE")
print("=" * 60)


# ---------------------------------------------------------
# Check files
# ---------------------------------------------------------

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

if not os.path.exists(WEIGHTS_FILE):
    raise FileNotFoundError(
        f"CROMA weights not found: {WEIGHTS_FILE}"
    )


print()
print("Input file:", INPUT_FILE)
print("CROMA weights:", WEIGHTS_FILE)


# ---------------------------------------------------------
# Load preprocessed Sentinel-1 data
# ---------------------------------------------------------

print()
print("Loading preprocessed SAR data...")

data = np.load(INPUT_FILE).astype(np.float32)

print("Loaded NumPy shape:", data.shape)
print("Data type:", data.dtype)


# ---------------------------------------------------------
# Verify dimensions
# ---------------------------------------------------------

if data.shape != (2, 120, 120):
    raise ValueError(
        f"Expected shape (2, 120, 120), "
        f"but got {data.shape}"
    )


# ---------------------------------------------------------
# Convert to PyTorch tensor
# ---------------------------------------------------------

x = torch.from_numpy(data).unsqueeze(0)

print()
print("Input tensor shape:", x.shape)
print("Input tensor dtype:", x.dtype)


# ---------------------------------------------------------
# Load pretrained CROMA Base
# ---------------------------------------------------------

print()
print("Loading pretrained CROMA Base...")
print("This may take some time on CPU...")

model = PretrainedCROMA(
    WEIGHTS_FILE,
    size="base",
    modality="SAR",
    image_resolution=120
)

model.eval()

print("CROMA loaded successfully.")


# ---------------------------------------------------------
# Run inference
# ---------------------------------------------------------

print()
print("Running CROMA inference...")
print("Please wait...")

with torch.no_grad():
    output = model(x)


# ---------------------------------------------------------
# Display outputs
# ---------------------------------------------------------

print()
print("CROMA inference completed.")

print()
print("Output keys:")
print(output.keys())

print()
print("SAR encodings shape:")
print(output["SAR_encodings"].shape)

print()
print("SAR GAP shape:")
print(output["SAR_GAP"].shape)


# ---------------------------------------------------------
# Extract embedding
# ---------------------------------------------------------

embedding = output["SAR_GAP"].cpu().numpy()

print()
print("CROMA embedding shape:")
print(embedding.shape)


# ---------------------------------------------------------
# Save embedding
# ---------------------------------------------------------

np.save(
    OUTPUT_FILE,
    embedding
)

print()
print("Embedding saved successfully:")
print(OUTPUT_FILE)


# ---------------------------------------------------------
# Verify
# ---------------------------------------------------------

saved = np.load(OUTPUT_FILE)

print()
print("Saved embedding shape:", saved.shape)
print("Embedding min:", saved.min())
print("Embedding max:", saved.max())
print("Embedding mean:", saved.mean())


print()
print("=" * 60)
print("CROMA INFERENCE COMPLETE")
print("=" * 60)