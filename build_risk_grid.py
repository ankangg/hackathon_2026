import numpy as np
import os

# ============================================================
# INITIALIZATION
# ============================================================
OUTPUT_GRID = r"data\risk_grid.npy"
os.makedirs("data", exist_ok=True)

print("=" * 70)
print("BUILDING ENVIRONMENTAL RISK GRID")
print("=" * 70)

# 1. Define Grid Dimensions (e.g., a 50x50 nautical mile sector)
GRID_SIZE = 50
print(f"Generating {GRID_SIZE}x{GRID_SIZE} spatial environment...")
np.random.seed(42)

# 2. Simulate Base Ice Risk
# In a real deployment, you would pass live SAR patches through your trained model.
# Here, we simulate a risk gradient from North to South.
ice_risk = np.linspace(10, 90, GRID_SIZE).reshape(-1, 1) + np.random.normal(0, 5, (GRID_SIZE, GRID_SIZE))
ice_risk = np.clip(ice_risk, 0, 100)

# 3. Integrate ERA5 Weather (Wind/Waves)
# Simulating a harsh weather front in the eastern section
print("Integrating ERA5 weather severity...")
weather_risk = np.zeros((GRID_SIZE, GRID_SIZE))
weather_risk[:, 35:] = np.random.uniform(50, 80, (GRID_SIZE, 15)) 

# 4. Integrate Iceberg Data
print("Plotting iceberg coordinates...")
iceberg_risk = np.zeros((GRID_SIZE, GRID_SIZE))
iceberg_locations = [(10, 15), (25, 25), (40, 10), (15, 35), (30, 40)]

for (r, c) in iceberg_locations:
    # Create a danger radius around the iceberg
    for i in range(-2, 3):
        for j in range(-2, 3):
            if 0 <= r+i < GRID_SIZE and 0 <= c+j < GRID_SIZE:
                iceberg_risk[r+i, c+j] = 100

# 5. Final Risk Calculation
# Formula: 50% Ice, 20% Weather, Override if Iceberg present
print("Calculating final navigational risk metrics...")
final_risk = (ice_risk * 0.5) + (weather_risk * 0.2)
final_risk = np.maximum(final_risk, iceberg_risk) # Icebergs overwrite underlying risk
final_risk = np.clip(final_risk, 0, 100)

# Save the grid for the A* Algorithm
np.save(OUTPUT_GRID, final_risk)

print("\n" + "=" * 70)
print(f"Risk grid successfully generated and saved to: {OUTPUT_GRID}")
print(f"Max Risk Node: {np.max(final_risk):.1f} | Min Risk Node: {np.min(final_risk):.1f}")
print("=" * 70)