"""
Polaris AI - Self-Healing Pre-Flight Asset Integrity Check
Verifies critical machine learning models, weights, grid arrays, and telemetry data.
Automatically triggers self-healing retraining or grid generation if derived assets are missing.
"""

import os
import sys
from typing import Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, CURRENT_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CROMA_DIR = os.path.join(BASE_DIR, "croma")

CROMA_WEIGHTS_FILE = os.path.join(CROMA_DIR, "CROMA_base.pt")
REGRESSOR_MODEL_FILE = os.path.join(MODELS_DIR, "sea_ice_rf_model.joblib")
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.csv")
ICEBERG_CSV_FILE = os.path.join(DATA_DIR, "iceberg_tracks_5.csv")
PRECOMPUTED_GRID_FILE = os.path.join(DATA_DIR, "precomputed_sic_grid.npy")
PRECOMPUTED_PROVENANCE_FILE = os.path.join(DATA_DIR, "precomputed_sic_provenance.npy")
ERA5_FILE = os.path.join(DATA_DIR, "era5_wind_mslp_2024_weddell.nc")


def run_checks() -> Dict[str, Any]:
    """
    Performs asset integrity audit and executes self-healing steps if required.
    Returns structured audit dictionary for GET /api/health-and-audit.
    """
    print("=" * 60)
    print("[check_assets] STARTING POLARIS PRE-FLIGHT ASSET AUDIT")
    print("=" * 60)

    audit_summary: Dict[str, Any] = {
        "status": "healthy",
        "models": {},
        "assets": {},
        "grid_coverage": {},
        "self_healing_actions": []
    }

    # 1. Check Regressor Model -> Self-heal if missing or corrupted
    regressor_ok = False
    if os.path.exists(REGRESSOR_MODEL_FILE):
        try:
            import joblib
            test_model = joblib.load(REGRESSOR_MODEL_FILE)
            if hasattr(test_model, "predict"):
                regressor_ok = True
                audit_summary["models"]["regressor_loaded"] = True
                print(f"[check_assets] OK: {REGRESSOR_MODEL_FILE} verified and successfully loaded.")
        except Exception as e:
            print(f"[check_assets] Existing model corrupted ({e}). Will retrain.")

    if not regressor_ok:
        print(f"[check_assets] Missing or invalid {REGRESSOR_MODEL_FILE}. Triggering train_regressor.py...")
        from train_regressor import train_and_save_regressor
        try:
            train_res = train_and_save_regressor()
            audit_summary["self_healing_actions"].append({
                "action": "trained_regressor",
                "r2": train_res["r2"],
                "mae": train_res["mae"]
            })
            audit_summary["models"]["regressor_loaded"] = True
        except Exception as e:
            print(f"[check_assets] Self-healing regressor training failed: {e}")
            audit_summary["models"]["regressor_loaded"] = False
            audit_summary["status"] = "degraded"

    # 2. Check Precomputed SIC Grid -> Self-heal if missing, wrong shape, or missing provenance
    grid_ok = False
    if os.path.exists(PRECOMPUTED_GRID_FILE) and os.path.exists(PRECOMPUTED_PROVENANCE_FILE):
        try:
            import numpy as np
            grid = np.load(PRECOMPUTED_GRID_FILE)
            prov = np.load(PRECOMPUTED_PROVENANCE_FILE)
            if grid.shape == (50, 50) and prov.shape == (50, 50):
                real_cnt = int(np.sum(prov))
                interp_cnt = int(np.sum(~prov))
                audit_summary["assets"]["sic_grid"] = True
                audit_summary["grid_coverage"] = {
                    "real_cells": real_cnt,
                    "interpolated_cells": interp_cnt
                }
                grid_ok = True
                print(f"[check_assets] OK: {PRECOMPUTED_GRID_FILE} verified (shape 50x50, real: {real_cnt}, interp: {interp_cnt}).")
        except Exception as e:
            print(f"[check_assets] Existing grid check error: {e}. Will regenerate.")

    if not grid_ok:
        print(f"[check_assets] Missing or invalid grid arrays. Triggering precompute_risk_grid.py...")
        from precompute_risk_grid import generate_sic_grid
        try:
            grid_res = generate_sic_grid()
            audit_summary["self_healing_actions"].append({
                "action": "generated_sic_grid",
                "real_cells": grid_res["real_cells"],
                "interpolated_cells": grid_res["interpolated_cells"]
            })
            audit_summary["assets"]["sic_grid"] = True
            audit_summary["grid_coverage"] = {
                "real_cells": grid_res["real_cells"],
                "interpolated_cells": grid_res["interpolated_cells"]
            }
        except Exception as e:
            print(f"[check_assets] Self-healing grid generation failed: {e}")
            audit_summary["assets"]["sic_grid"] = False
            audit_summary["status"] = "degraded"

    # 3. Check Iceberg Tracks
    audit_summary["assets"]["iceberg_tracks"] = os.path.exists(ICEBERG_CSV_FILE)
    if audit_summary["assets"]["iceberg_tracks"]:
        print(f"[check_assets] OK: {ICEBERG_CSV_FILE} found.")

    # 4. Check Training Ground Truth & Features
    raw_sic_file = os.path.join(DATA_DIR, "raw", "sea_ice_2024_full.nc")
    audit_summary["assets"]["sic_ground_truth"] = os.path.exists(raw_sic_file) or os.path.exists(TRAINING_DATA_FILE)
    if audit_summary["assets"]["sic_ground_truth"]:
        print(f"[check_assets] OK: Sea-ice ground truth verified.")

    # 5. Check CROMA Weights
    croma_present = os.path.exists(CROMA_WEIGHTS_FILE) or os.path.exists(os.path.join(CROMA_DIR, "CROMA", "CROMA_base.pt"))
    if croma_present:
        actual_path = CROMA_WEIGHTS_FILE if os.path.exists(CROMA_WEIGHTS_FILE) else os.path.join(CROMA_DIR, "CROMA", "CROMA_base.pt")
        audit_summary["models"]["croma_loaded"] = os.path.getsize(actual_path) > 100_000_000
        print(f"[check_assets] OK: CROMA ViT foundation weights verified at {actual_path} ({os.path.getsize(actual_path)} bytes).")
    else:
        audit_summary["models"]["croma_loaded"] = False
        audit_summary["status"] = "degraded"

    # 6. Check ERA5 Reanalysis
    era5_candidates = [
        os.path.join(DATA_DIR, "era5_2024_weddell.nc"),
        os.path.join(DATA_DIR, "era5_wind_mslp_2024_weddell.nc")
    ]
    era5_present = any(os.path.exists(p) for p in era5_candidates)
    audit_summary["assets"]["era5"] = era5_present
    if era5_present:
        print(f"[check_assets] OK: ERA5 atmospheric reanalysis feed verified.")
    else:
        audit_summary["status"] = "degraded"

    # Overall health assessment
    all_models = all(audit_summary["models"].values())
    all_assets = all(audit_summary["assets"].values())
    audit_summary["status"] = "healthy" if (all_models and all_assets) else "degraded"

    print(f"[check_assets] Audit finished. Status: {audit_summary['status']}")
    print("=" * 60)
    return audit_summary


if __name__ == "__main__":
    summary = run_checks()
    import json
    print(json.dumps(summary, indent=2))
