# 02_BACKEND_CLAUDE_INSTRUCTIONS.md
## Polaris AI — Backend Specification (for Claude / backend implementation)

You are building the entire `/backend` service for Polaris AI: a FastAPI application that
re-platforms the logic currently living in the monolithic Streamlit prototype `app.py`
into a decoupled API consumed by a separate Next.js frontend. Read `app.py` in full before
writing anything — it is the validated reference implementation for every formula and
threshold below. You are porting proven logic, not redesigning it.

No placeholder logic. No `np.random` fills. No hardcoded sample responses standing in for
real model output. Every response must be the actual result of running the real pipeline
against the real assets in `croma/`, `models/`, and `data/`.

---

## 1. Directory Structure (must match exactly)

```
backend/
├── main.py                    # FastAPI server & route orchestration
├── precompute_risk_grid.py    # Spatial feature extraction & grid mapping
├── physics_engine.py          # ERA5 wind parsing & iceberg force-balance drift
├── pathfinding.py             # 8-directional A* algorithm implementation
├── train_regressor.py         # Self-healing fallback model trainer
├── check_assets.py            # Pre-flight asset integrity & auto-execution script
└── requirements.txt           # Python dependencies
```

`requirements.txt` must include at minimum: `fastapi`, `uvicorn[standard]`, `pydantic`,
`torch`, `scikit-learn`, `xarray`, `netCDF4`, `numpy`, `joblib`, `pandas`, `scipy`
(for nearest-neighbor interpolation).

---

## 2. Geographic & Grid Constants

Define these once, in a shared location (e.g. top of `precompute_risk_grid.py` or a small
`constants.py`), and import everywhere rather than re-declaring magic numbers:

```python
LAT_MAX, LAT_MIN = -65.0, -70.0   # degrees S
LON_MIN, LON_MAX = -50.0, -40.0   # degrees W
GRID_SIZE = 50                     # 50 x 50 spatial matrix
```

### Coordinate ↔ matrix index transform (must match `app.py` exactly)

```python
def latlon_to_index(lat: float, lon: float) -> tuple[int, int]:
    r = int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (GRID_SIZE - 1))
    c = int((lon - LON_MIN) / (LON_MAX - LON_MIN) * (GRID_SIZE - 1))
    return r, c
```

The inverse (index → lat/lon) is required for mapping A* output waypoints back to GPS
coordinates for the API response — implement and use it rather than re-deriving inline.

---

## 3. Vision & ML Regressor Pipeline (`precompute_risk_grid.py`, `train_regressor.py`)

1. Load `croma/CROMA_base.pt` (pretrained CROMA Vision Transformer) in inference mode
   (frozen weights, no gradient computation — wrap inference in `torch.no_grad()`).
2. For each SAR patch in `data/sentinel1/patches/` (120×120 px), run it through CROMA to
   produce a 768-dimensional latent embedding.
3. Load `models/sea_ice_rf_model.joblib` (PCA + L2 Ridge Regressor pipeline). If this file
   is missing, this is the trigger condition for `train_regressor.py` (see Section 7) —
   `main.py` and `precompute_risk_grid.py` should never train inline; they should call out
   to `check_assets.py`'s self-healing path instead.
4. Feed each 768-dim embedding through the regressor to predict Sea Ice Concentration
   (SIC), a percentage in `[0, 100]`.
5. Map each patch's predicted SIC onto its corresponding cell(s) in the 50×50 grid using
   the coordinate transform in Section 2.
6. For grid cells with no direct patch coverage, fill via **nearest-neighbor spatial
   interpolation** over the cells that do have real predictions (e.g.
   `scipy.spatial.cKDTree` or `scipy.interpolate.griddata(method="nearest")`). Track which
   cells were real vs. interpolated — this distinction is required later for the
   `grid_coverage` metric in the API response. **Never fill uncovered cells with a uniform
   random value or a constant.**
7. Persist the resulting grid to `data/precomputed_sic_grid.npy` (shape `(50, 50)`), plus a
   parallel boolean/int mask array (or an extra channel) recording real-vs-interpolated
   provenance per cell, so `main.py` doesn't have to recompute coverage stats from scratch
   on every request.

### `train_regressor.py` (self-healing fallback trainer)

Only invoked when `models/sea_ice_rf_model.joblib` is missing. Must:
1. Extract CROMA embeddings for all patches in `data/sentinel1/patches/` (reuse the
   extraction logic from step 1–2 above; don't duplicate it — factor it into a shared
   helper both files import).
2. Load ground-truth SIC values from `data/raw/sea_ice_2024_full.nc` (NOAA-NSIDC, via
   `xarray`), aligned to each patch's coordinates.
3. Fit a PCA (dimensionality reduction) + L2-regularized Ridge Regressor pipeline
   (`sklearn.pipeline.Pipeline`) on embeddings → SIC.
4. Hold out a test split (do not report training-set accuracy as the headline metric) and
   compute **R²** and **MAE** on the held-out split.
5. Log both metrics to stdout in a clearly greppable format (e.g.
   `"[train_regressor] R2=0.xx MAE=x.xx"`) so `check_assets.py`/the verification report can
   capture them.
6. Serialize the fitted pipeline to `models/sea_ice_rf_model.joblib` via `joblib.dump`.

---

## 4. Force-Balanced Iceberg Drift Physics (`physics_engine.py`)

1. Load ERA5 reanalysis wind data from `data/era5_2024_weddell.nc` via `xarray`, extracting
   `u10` and `v10` (10m wind components) for the relevant time and location.
2. Load historical iceberg base positions from `data/iceberg_tracks_5.csv` (BYU/NIC
   tracks).
3. Compute the iceberg velocity vector as a weighted combination of ocean current and wind
   drag:

   ```
   v_iceberg = alpha * v_ocean + beta * v_wind
   ```

   Use empirically reasonable drag coefficients for `alpha`/`beta` consistent with
   `app.py`'s existing offset model:

   ```
   delta_lat = 0.008 * (delta_t_hours / 24)
   delta_lon = 0.015 * (delta_t_hours / 24)
   ```

   where `delta_t_hours` is the user-supplied `hours_offset` (0–72). Scale/modulate this
   base displacement by the actual ERA5 wind magnitude/direction at each iceberg's current
   position rather than treating the 0.008/0.015 constants as wind-independent — the point
   of the physics engine is that drift responds to the *live* ERA5 data, not just elapsed
   time.
4. Project each drifted iceberg's core position, plus its immediate 3×3 grid neighborhood,
   onto the risk grid as **hard obstacles**: `Risk = 100` for those cells (this is
   intentional — see Section 6 for the rationale to preserve in code comments/docstrings:
   a tracked iceberg is a near-certain hazard, so it's treated as an absolute exclusion
   zone, not a soft probability).
5. Expose a single function, e.g. `get_iceberg_obstacles(hours_offset, weather_severity) ->
   list[tuple[int, int]]`, returning the grid indices to hard-set to Risk=100. `main.py`
   and `pathfinding.py` should call this rather than re-deriving drift logic themselves.
6. Also expose the resolved `wind_vector` (`u10`, `v10`, and derived `speed_ms =
   sqrt(u10**2 + v10**2)`) used for the current request, since the API response must report
   the *exact* wind vector applied (see Section 8's response schema) — do not report a
   generic/average value when the response schema asks for the value actually used in this
   computation.

---

## 5. Dynamic Risk Matrix Fusion

Combine the SIC grid (Section 3) with weather severity into a per-cell risk score before
obstacle-stamping:

```
Cell Risk = (SIC * 0.6) + (Weather Risk * 0.2 * weather_severity_factor)
```

Then apply the hard iceberg exclusion zones from `physics_engine.py` on top, overwriting
any fused score in those cells with `100`. The `weather_severity_factor` is the
user-supplied slider value (0.5–2.5) from the request payload — apply it directly, don't
clamp or silently rescale it beyond documenting any clamping you consider necessary for
numerical stability.

---

## 6. A* Pathfinding Engine (`pathfinding.py`)

- 8-directional (cardinal + diagonal) graph search over the fused 50×50 risk grid.
- Heuristic: Euclidean distance from current node `(r, c)` to goal `(r_goal, c_goal)`.
- Edge cost:

  ```
  Edge Cost = Δdistance + 0.45 * Risk Score
  ```

  where `Δdistance` is `1.0` for cardinal moves and `1.414` (√2) for diagonal moves.
- **Hard safety constraint:** any cell with `Risk >= 95` is treated as impassable
  (`cost = infinity`) and must never appear in a returned path, regardless of whether a
  technically lower-total-cost route would cross it. Implement this as an early skip in
  the neighbor-expansion step, not as a very large finite penalty that could theoretically
  still be chosen.
- Implement with a priority queue (`heapq`), tracking `g(n)` (cost so far) per node and
  reconstructing the path via a `came_from` map once the goal is popped.
- If no path exists (goal unreachable without crossing Risk ≥ 95), return a clear failure
  signal (e.g. `None` / raise a specific exception) that `main.py` converts into a
  `status: "failed"` API response with an honest message — never fall back to a route that
  silently crosses a hard-excluded cell just to return "something."
- Map the resulting sequence of grid indices back to `(lat, lon)` pairs using the inverse
  of the transform in Section 2 before returning.

---

## 7. Self-Healing Pre-Flight Check (`check_assets.py`)

Runs before `main.py` starts serving traffic (invoke it at the top of `main.py`'s startup,
or as a separate script Antigravity runs first — implement both: an importable
`run_checks()` function `main.py` calls on FastAPI startup, and a `if __name__ ==
"__main__"` block so it's also runnable standalone).

Logic:
1. Check every path in Section 1/the blueprint's file inventory (CROMA weights, joblib
   model, SAR patches directory, ERA5 `.nc`, ground-truth `.nc`, iceberg CSV,
   precomputed grid `.npy`).
2. If `models/sea_ice_rf_model.joblib` is missing → call `train_regressor.py`'s training
   routine, wait for it to complete, then re-check.
3. If `data/precomputed_sic_grid.npy` is missing → call `precompute_risk_grid.py`'s grid
   generation routine, then re-check.
4. Return/log a structured summary (dict) of what was found, what was missing, and what
   was auto-generated — this feeds directly into `GET /api/health-and-audit` (Section 8)
   and into `VERIFICATION_REPORT.md`.
5. If any asset is missing *and* cannot be auto-generated (e.g. the raw SAR patches
   themselves are entirely absent, so there's nothing to train on), fail loudly with a
   specific, actionable error message rather than starting the server in a broken state.

---

## 8. FastAPI Endpoints (`main.py`)

Apply CORS middleware allowing the Next.js dev origin (`http://localhost:3000`) **and the
real deployed frontend domain** (e.g. `https://polaris-ai.vercel.app`) — this project is
being deployed publicly, not run locally only, so the production origin must be in the
allow-list before launch, not added as an afterthought.

**Strict serialization guard:** immediately before constructing any Pydantic response
model, explicitly cast every NumPy scalar/array touching it: `float(x)`, `int(x)`,
`arr.tolist()`, `bool(x)`. Do this at the boundary function, not scattered ad hoc — write
one small helper (e.g. `to_native(x)`) and use it consistently.

### `GET /api/health-and-audit`

Returns model-loading state, file asset integrity (from `check_assets.py`), ERA5
availability, and grid coverage statistics (real vs. interpolated cell counts from the
precomputed grid's provenance mask). Example shape:

```json
{
  "status": "healthy",
  "models": { "croma_loaded": true, "regressor_loaded": true },
  "assets": { "era5": true, "sic_ground_truth": true, "iceberg_tracks": true, "sic_grid": true },
  "grid_coverage": { "real_cells": 1850, "interpolated_cells": 650 }
}
```

### `POST /api/safest-route`

Request (Pydantic model, validate lat/lon ranges against the operational bounding box and
`hours_offset`/`weather_severity` against their documented ranges, returning HTTP 422 with
a clear message on violation):

```json
{
  "start_lat": -65.2,
  "start_lon": -49.5,
  "goal_lat": -69.8,
  "goal_lon": -40.5,
  "hours_offset": 24,
  "weather_severity": 1.2
}
```

Response on success:

```json
{
  "status": "success",
  "waypoints": [[-65.2, -49.5], [-65.4, -49.2]],
  "metrics": {
    "total_waypoints": 34,
    "wind_vector": { "u10": 4.12, "v10": -2.85, "speed_ms": 5.01 },
    "average_risk": 28.4,
    "grid_coverage": { "real_cells": 1850, "interpolated_cells": 650 }
  }
}
```

Response on unreachable goal (per Section 6): `status: "failed"` plus a human-readable
`message` field explaining that no route avoiding Risk ≥ 95 cells exists between the given
points, with no `waypoints` fabricated.

Orchestration inside this endpoint, in order: validate input → get fused risk grid for the
requested `hours_offset`/`weather_severity` (Sections 4–5) → run A* (Section 6) → compute
`average_risk` as the mean fused-risk value along the returned path cells → assemble and
return the response through the serialization guard.

---

## 9. Traceability for the Verification Report

When you finish, be able to point to (and expect this to be asked for explicitly):
- The exact file and line number where the regressor's `.predict()` output is written into
  the fused risk grid that `pathfinding.py` consumes.
- The exact file and line number where `Risk >= 95` is enforced as impassable in the A*
  neighbor expansion.
- The R² and MAE logged by `train_regressor.py`, if it ran.

Keep these citable — i.e. don't bury the SIC-into-grid assignment inside a dense one-liner
that's hard to point to; give it its own clearly named line/function.

---

## 10. Local Run & Smoke Test, Then Deployment

Local run (checkpoint, not the finished deliverable):

```bash
cd backend
pip install -r requirements.txt
python check_assets.py        # confirm self-healing pass completes cleanly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then, from another shell:

```bash
curl http://localhost:8000/api/health-and-audit
curl -X POST http://localhost:8000/api/safest-route \
  -H "Content-Type: application/json" \
  -d '{"start_lat":-65.2,"start_lon":-49.5,"goal_lat":-69.8,"goal_lon":-40.5,"hours_offset":24,"weather_severity":1.2}'
```

Confirm both return well-formed JSON with real, non-null, non-placeholder values before
considering the backend logic done.

**Then deploy.** Read `main.py`'s port binding from the `PORT` environment variable (most
hosts inject this rather than letting you fix `8000`), deploy to a host that can run a
persistent Python/PyTorch process (Render, Railway, Fly.io, or an equivalent), and ensure
all model/data assets are actually included in the deployed build (not excluded by
`.gitignore`/`.dockerignore` and silently missing in production). Update the CORS
allow-list to include the deployed frontend's real domain, not just `localhost:3000`.
Re-run the two `curl` checks above against the live deployed URL before considering the
backend finished — a local-only success does not satisfy the project requirements.