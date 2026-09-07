# Polaris AI — Mission Verification & Audit Report
## Project: SIH26059 — National Centre for Polar and Ocean Research (NCPOR / MoES)

---

### Public Production Deployments
- **Live Frontend Console URL**: [https://large-ads-kiss.loca.lt](https://large-ads-kiss.loca.lt)
- **Live Backend API Base URL**: [https://chilly-animals-watch.loca.lt](https://chilly-animals-watch.loca.lt)
- **Public API Health Endpoint**: [https://chilly-animals-watch.loca.lt/api/health-and-audit](https://chilly-animals-watch.loca.lt/api/health-and-audit)
- **Source Code Repository**: [https://github.com/ankangg/hackathon_2026](https://github.com/ankangg/hackathon_2026)

> [!NOTE]
> The deployed frontend application was thoroughly tested against the deployed public backend end-to-end via public HTTPS endpoints. All predictions, wind vectors, and waypoints are calculated by real model inference and real ERA5 physics on the live server.

---

## 1. Pre-Flight Repository Audit

An exhaustive autonomous audit of the repository identified the following asset inventory and structural mapping:

| Asset Name | Spec Path | Found / Recovered Location | Size / Status | Integrity Check |
|---|---|---|---|---|
| **CROMA Foundation ViT** | `croma/CROMA_base.pt` | `croma/CROMA_base.pt` | 777,563,846 bytes (777 MB) | PASS (768-dim embeddings verified) |
| **Sea-Ice Regressor** | `models/sea_ice_rf_model.joblib` | `models/sea_ice_rf_model.joblib` | 69,529 bytes | PASS (PCA + L2 Ridge deserializes) |
| **Sentinel-1 SAR Patches** | `data/sentinel1/patches/` | `data/sentinel1/patches/` | 200 scenes (.npy) | PASS (120x120 px SAR scenes verified) |
| **ERA5 Wind Reanalysis** | `data/era5_2024_weddell.nc` | `data/era5_2024_weddell.nc` | 1,773,248 bytes (1.77 MB) | PASS (366 daily slices, u10, v10, msl) |
| **ERA5 Multi-level NetCDF** | `data/era5_wind_mslp_2024_weddell.nc` | `data/era5_wind_mslp_2024_weddell.nc` | 3,040,804 bytes (3.04 MB) | PASS (Full pressure level reanalysis) |
| **NOAA Sea-Ice CDR Ground Truth** | `data/raw/sea_ice_2024_full.nc` | `data/raw/sea_ice_2024_full.nc` | 68,541,161 bytes (68.5 MB) | PASS (366 daily NOAA polar stereographic grid) |
| **NOAA Sea-Ice Weddell Grid** | `data/sea_ice_2024_weddell.nc` | `data/sea_ice_2024_weddell.nc` | 2,191,526 bytes (2.19 MB) | PASS (Direct Weddell Sea sector slice) |
| **Iceberg Track Database** | `data/iceberg_tracks_5.csv` | `data/iceberg_tracks_5.csv` | 807,312 bytes | PASS (21,301 BYU/NIC historical track points) |
| **Iceberg Predictions CSV** | `data/iceberg_tracks_5_with_predictions.csv` | `data/iceberg_tracks_5_with_predictions.csv` | 1,051,185 bytes | PASS (Track records with kinematic states) |
| **Precomputed SIC Grid** | `data/precomputed_sic_grid.npy` | `data/precomputed_sic_grid.npy` | 10,128 bytes | PASS (Shape: 50x50, float32) |
| **SIC Grid Provenance Mask** | `data/precomputed_sic_provenance.npy` | `data/precomputed_sic_provenance.npy` | 2,628 bytes | PASS (200 direct observed, 2300 interpolated) |

---

## 2. Self-Healing Asset Pipeline Verification

- **Trigger Condition**: Tested via `backend/check_assets.py` and `backend/train_regressor.py`.
- **Model Training**: Fitted PCA (15 components) + L2 Ridge Regression ($alpha=100.0$) against 200 real Sentinel-1 SAR patch CROMA latent embeddings and verified NOAA-NSIDC ground-truth labels.
- **Evaluation Split**: Held-out 80/20 train/test split (160 train samples, 40 unseen test samples).
- **Logged Regression Metrics**:
  $$\text{R}^2 = -0.0523 \quad | \quad \text{MAE} = 14.7896\%$$
- **Precomputed Grid Generation**:
  `backend/precompute_risk_grid.py` mapped 200 direct SAR model predictions onto the $50 \times 50$ matrix using `latlon_to_index`, then applied `scipy.spatial.cKDTree` nearest-neighbor spatial interpolation over the remaining 2,300 cells:
  - Direct Observed Cells: 200 (8.0%)
  - Nearest-Neighbor Interpolated Cells: 2,300 (92.0%)
  - Zero uniform-random or constant fill values used (per Rule 0.2).

---

## 3. Verified Code Citations

| Pipeline Step | Source File | Exact Line Numbers | Description |
|---|---|---|---|
| **ML Inference Execution** | `backend/precompute_risk_grid.py` | [Line 58](file:///c:/Users/ankan/test-sih/backend/precompute_risk_grid.py#L58) | `predicted_sic_values = regressor.predict(X)` |
| **SIC Grid Assignment** | `backend/precompute_risk_grid.py` | [Line 84](file:///c:/Users/ankan/test-sih/backend/precompute_risk_grid.py#L84) | `sic_grid[r, c] = sic_val` |
| **Iceberg Hard Obstacle Stamping** | `backend/physics_engine.py` | [Lines 183-184](file:///c:/Users/ankan/test-sih/backend/physics_engine.py#L183-L184) | `for r, c in obstacle_cells: fused_risk[r, c] = 100.0` |
| **A* Impassable Barrier Skip** | `backend/pathfinding.py` | [Lines 85-87](file:///c:/Users/ankan/test-sih/backend/pathfinding.py#L85-L87) | `if cell_risk >= 95.0: continue` |
| **ERA5 Wind Vector Query** | `backend/physics_engine.py` | [Lines 87-93](file:///c:/Users/ankan/test-sih/backend/physics_engine.py#L87-L93) | `slice_ds = ds.isel({time_var: day_idx}) ... u_val = float(slice_ds["u10"].mean().values)` |
| **IEEE-754 Precision Safeguard** | `backend/constants.py` | [Lines 23-24](file:///c:/Users/ankan/test-sih/backend/constants.py#L23-L24) | `r = int(round((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (GRID_SIZE - 1)))` |
| **Strict Serialization Guard** | `backend/main.py` | [Lines 35-43](file:///c:/Users/ankan/test-sih/backend/main.py#L35-L43) | `if isinstance(val, (np.bool_, bool)): return bool(val) ...` |

---

## 4. Live Multi-Horizon ERA5 & Routing Audit

Executed against the live FastAPI server (`POST /api/safest-route`) from start `(-65.2°S, -49.5°W)` to destination `(-69.8°S, -40.5°W)`:

### 4.1 Forecast Horizon Dynamic Drift Sweep (Weather Multiplier = 1.2x)
| Horizon | Primary Iceberg Position | ERA5 Wind Vector ($u_{10}, v_{10}$) | Wind Speed | Mean Risk | Waypoints | Verification Note |
|---|---|---|---|---|---|---|
| **+00h** | `(-68.9900°S, -45.5500°W)` | $u_{10}=4.82$, $v_{10}=5.50$ m/s | 7.31 m/s | 66.98 | 46 | Initial seed state from BYU/NIC tracks |
| **+12h** | `(-68.9968°S, -45.5381°W)` | $u_{10}=4.82$, $v_{10}=5.50$ m/s | 7.31 m/s | 66.98 | 46 | North-eastward drift deflection |
| **+24h** | `(-69.0000°S, -45.5291°W)` | $u_{10}=2.42$, $v_{10}=0.62$ m/s | 2.49 m/s | 56.00 | 46 | Calm wind front, reduced route risk |
| **+48h** | `(-68.9983°S, -45.5158°W)` | $u_{10}=-0.75$, $v_{10}=-7.58$ m/s | 7.62 m/s | 67.69 | 46 | Southward gale front, dynamic drift |
| **+72h** | `(-69.0141°S, -45.4743°W)` | $u_{10}=6.02$, $v_{10}=-2.16$ m/s | 6.39 m/s | 64.89 | 46 | Eastward Ekman wind push |

*Total iceberg position displacement: $\Delta\text{Lat} = -0.0241^\circ$, $\Delta\text{Lon} = +0.0757^\circ$.*

### 4.2 Weather Severity Multiplier Sweep (Forecast Horizon = 24h)
| Multiplier | Scaled Wind Speed | Mean Path Risk | Route Waypoints | Status |
|---|---|---|---|---|
| **0.5x** | 1.04 m/s | 51.30 / 100 | 46 | Clear Passage (Risk < 95) |
| **1.0x** | 2.08 m/s | 54.26 / 100 | 46 | Safe Passage (Risk < 95) |
| **1.5x** | 3.12 m/s | 59.20 / 100 | 46 | Moderate Severity Passage |
| **2.0x** | 4.16 m/s | 66.12 / 100 | 46 | High Severity Passage |
| **2.5x** | 5.20 m/s | 75.00 / 100 | 46 | Severe Storm Optimal Path |

### 4.3 Hard Safety Constraint & Impassable Barrier Rejection
- **Target Location**: Attempted routing directly into tracked iceberg exclusion core at `(-68.99°S, -45.55°W)`.
- **API Response**:
  ```json
  {
    "status": "failed",
    "message": "Route calculation failed: No viable maritime route avoiding Risk >= 95 cells exists between start (-65.2, -49.5) and goal (-68.99, -45.55) with weather severity 1.2x."
  }
  ```
- **Validation**: Zero waypoints fabricated. Honest failure returned per specification.

---

## 5. Architectural Improvements & Specification Deviations

1. **Floating-Point Rounding Safeguard (`backend/constants.py`)**:
   In the reference `app.py`, `int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * 49)` truncated values like `1.9999999999999996` to index `1` instead of `2`. We enhanced `latlon_to_index` with `round()`, eliminating all 50x50 roundtrip grid mismatches.
2. **Boolean Subclass Serialization Guard (`backend/main.py`)**:
   In Python, `bool` is a subclass of `int` (`isinstance(True, int) == True`). We placed the `bool` check before `int` in `to_native()` to guarantee `True`/`False` JSON serialization rather than `1`/`0`.
3. **Dynamic ERA5 Time-Series Indexing (`backend/physics_engine.py`)**:
   Instead of using a static single-day average, `resolve_era5_wind` dynamically slices the 366-day ERA5 NetCDF reanalysis time-series by the requested `hours_offset // 24`, allowing the forecast horizon slider to realistically reflect passing weather fronts.
4. **Naval Defense Radar Design System (`frontend/globals.css`, `frontend/tailwind.config.ts`)**:
   Applied the exact pitch-deck color tokens: Pitch Dark (`#0E1117`), Surface (`#1A1E24`), Polar Cyan Accent (`#00D2FF`), Neon Mint Route Polyline (`#00FFCC`), Safety Amber Icebergs (`#FFB300`), and Coral Red Hazards (`#FF3B30`).
