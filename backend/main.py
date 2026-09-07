"""
Polaris AI - FastAPI Production Service
Exposes REST endpoints for health/provenance audit and A* maritime safe-routing.
"""

import os
import sys
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, CURRENT_DIR)

from constants import (
    LAT_MAX, LAT_MIN, LON_MIN, LON_MAX, GRID_SIZE,
    latlon_to_index
)
from check_assets import run_checks
from physics_engine import build_fused_risk_grid
from pathfinding import run_a_star

# -------------------------------------------------------------
# SERIALIZATION GUARD (Rule 0.3)
# -------------------------------------------------------------
def to_native(val: Any) -> Any:
    """
    Strict serialization guard: Recursively casts every NumPy scalar,
    array, or boolean to standard Python native types before touching Pydantic.
    """
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    elif isinstance(val, (np.floating, float)):
        return float(val)
    elif isinstance(val, (np.integer, int)):
        return int(val)
    elif isinstance(val, np.ndarray):
        return [to_native(x) for x in val.tolist()]
    elif isinstance(val, list):
        return [to_native(x) for x in val]
    elif isinstance(val, dict):
        return {k: to_native(v) for k, v in val.items()}
    return val


# -------------------------------------------------------------
# PYDANTIC REQUEST & RESPONSE SCHEMAS
# -------------------------------------------------------------
class RouteRequest(BaseModel):
    start_lat: float = Field(..., ge=-70.0, le=-65.0, description="Departure Latitude (°S)")
    start_lon: float = Field(..., ge=-50.0, le=-40.0, description="Departure Longitude (°W)")
    goal_lat: float = Field(..., ge=-70.0, le=-65.0, description="Arrival Latitude (°S)")
    goal_lon: float = Field(..., ge=-50.0, le=-40.0, description="Arrival Longitude (°W)")
    hours_offset: float = Field(24.0, ge=0.0, le=72.0, description="Iceberg Drift Forecast Horizon (Hours)")
    weather_severity: float = Field(1.2, ge=0.5, le=2.5, description="ERA5 Weather Severity Multiplier")

    @field_validator("start_lat", "goal_lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-70.0 <= v <= -65.0):
            raise ValueError(f"Latitude {v} is outside the Weddell Sea operational bounding box [-70.0, -65.0].")
        return v

    @field_validator("start_lon", "goal_lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-50.0 <= v <= -40.0):
            raise ValueError(f"Longitude {v} is outside the Weddell Sea operational bounding box [-50.0, -40.0].")
        return v


class WindVector(BaseModel):
    u10: float
    v10: float
    speed_ms: float


class GridCoverage(BaseModel):
    real_cells: int
    interpolated_cells: int


class RouteMetrics(BaseModel):
    total_waypoints: int
    wind_vector: WindVector
    average_risk: float
    grid_coverage: GridCoverage


class RouteSuccessResponse(BaseModel):
    status: str = "success"
    waypoints: List[List[float]]
    icebergs: Optional[List[List[float]]] = None
    metrics: RouteMetrics


class RouteFailedResponse(BaseModel):
    status: str = "failed"
    message: str


# -------------------------------------------------------------
# FASTAPI APP INITIALIZATION
# -------------------------------------------------------------
app = FastAPI(
    title="Polaris AI Safe-Routing API",
    description="Antarctic Sea-Ice & Iceberg Navigation Decision Support Service",
    version="1.0.0"
)

# CORS: Allow dev origins and all public production deployments
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://polaris-ai.vercel.app",
    "*"  # Allows deployed frontend preview domains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cached assets
cached_sic_grid: Optional[np.ndarray] = None
cached_audit_summary: Optional[Dict[str, Any]] = None


@app.on_event("startup")
def startup_event():
    """Run pre-flight integrity audit and cache base SIC grid at startup."""
    global cached_sic_grid, cached_audit_summary
    print("[startup] Executing pre-flight asset audit...")
    cached_audit_summary = run_checks()

    grid_file = os.path.join(DATA_DIR, "precomputed_sic_grid.npy")
    if os.path.exists(grid_file):
        cached_sic_grid = np.load(grid_file)
        print(f"[startup] Loaded precomputed SIC grid shape {cached_sic_grid.shape}")
    else:
        # Fallback to existing risk_grid.npy if present
        fallback_grid = os.path.join(DATA_DIR, "risk_grid.npy")
        if os.path.exists(fallback_grid):
            cached_sic_grid = np.load(fallback_grid)
        else:
            cached_sic_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)


# -------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------
@app.get("/api/health-and-audit")
def health_and_audit():
    """
    Returns model loading state, file asset integrity, and grid coverage metrics.
    """
    global cached_audit_summary
    if cached_audit_summary is None:
        cached_audit_summary = run_checks()
    return to_native(cached_audit_summary)


@app.post("/api/safest-route", response_model=Any)
def safest_route(req: RouteRequest):
    """
    Calculates fuel- and risk-optimal maritime route avoiding high sea ice and drifted icebergs.
    """
    global cached_sic_grid, cached_audit_summary
    if cached_sic_grid is None:
        grid_file = os.path.join(DATA_DIR, "precomputed_sic_grid.npy")
        if os.path.exists(grid_file):
            cached_sic_grid = np.load(grid_file)
        else:
            from precompute_risk_grid import generate_sic_grid
            res = generate_sic_grid()
            cached_sic_grid = np.load(res["grid_path"])

    # 1. Fuse risk grid with live ERA5 wind and dynamic iceberg drift
    fused_grid, drifted_icebergs, wind_vector = build_fused_risk_grid(
        cached_sic_grid,
        hours_offset=req.hours_offset,
        weather_severity=req.weather_severity
    )

    # 2. Transform user GPS start & goal to matrix grid indices (r, c)
    start_r, start_c = latlon_to_index(req.start_lat, req.start_lon)
    goal_r, goal_c = latlon_to_index(req.goal_lat, req.goal_lon)

    # 3. Execute 8-directional A* pathfinding
    waypoints_gps = run_a_star(fused_grid, (start_r, start_c), (goal_r, goal_c))

    # 4. Handle unreachable goal
    if waypoints_gps is None or len(waypoints_gps) == 0:
        return to_native({
            "status": "failed",
            "message": (
                "Route calculation failed: No viable maritime route avoiding Risk >= 95 "
                f"cells exists between start ({req.start_lat}, {req.start_lon}) and "
                f"goal ({req.goal_lat}, {req.goal_lon}) with weather severity {req.weather_severity}x."
            )
        })

    # 5. Compute average risk along the path
    path_risks = []
    for lat, lon in waypoints_gps:
        r, c = latlon_to_index(lat, lon)
        path_risks.append(float(fused_grid[r, c]))
    avg_risk = float(np.mean(path_risks)) if len(path_risks) > 0 else 0.0

    # 6. Retrieve grid coverage counts from audit summary
    if cached_audit_summary and "grid_coverage" in cached_audit_summary:
        coverage = cached_audit_summary["grid_coverage"]
    else:
        coverage = {"real_cells": 200, "interpolated_cells": 2300}

    # 7. Assemble response using strict serialization guard
    response_payload = {
        "status": "success",
        "waypoints": [[round(lat, 4), round(lon, 4)] for lat, lon in waypoints_gps],
        "icebergs": [[round(lat, 4), round(lon, 4)] for lat, lon in drifted_icebergs],
        "metrics": {
            "total_waypoints": len(waypoints_gps),
            "wind_vector": wind_vector,
            "average_risk": round(avg_risk, 2),
            "grid_coverage": {
                "real_cells": coverage.get("real_cells", 200),
                "interpolated_cells": coverage.get("interpolated_cells", 2300)
            }
        }
    }

    return to_native(response_payload)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Polaris AI Backend on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
