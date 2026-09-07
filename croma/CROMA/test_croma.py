import torch
from use_croma import PretrainedCROMA

print("Loading CROMA...")
model = PretrainedCROMA(
    "CROMA_base.pt",
    size="base",
    modality="SAR",
    image_resolution=120
)

print("CROMA loaded!")

# Create a fake Sentinel-1 SAR image
# CROMA expects: [batch, 2 channels, 120, 120]
sar_image = torch.randn(1, 2, 120, 120)

print("Running inference...")

with torch.no_grad():
    features = model(sar_image)

print("Inference complete!")
print("Output type:", type(features))

if isinstance(features, dict):
    print("Output keys:", features.keys())
    for key, value in features.items():
        if torch.is_tensor(value):
            print(key, "shape:", value.shape)
else:
    print("Output shape:", features.shape)