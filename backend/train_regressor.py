"""
Polaris AI - Self-Healing Sea-Ice Regressor Trainer
Fits PCA (dimensionality reduction) + L2-regularized Ridge Regressor pipeline
on 768-dim CROMA ViT embeddings -> Sea Ice Concentration (SIC) percentage.
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

# Ensure root paths resolve properly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.csv")
MODEL_OUTPUT_FILE = os.path.join(MODELS_DIR, "sea_ice_rf_model.joblib")


def train_and_save_regressor(data_path: str = TRAINING_DATA_FILE, output_path: str = MODEL_OUTPUT_FILE) -> dict:
    """
    Trains the PCA + Ridge Regression pipeline on real CROMA features and NOAA sea-ice labels.
    Logs R2 and MAE to stdout in a greppable format and serializes the model.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Ground truth training data not found at {data_path}. "
            "Cannot train regressor without verified training set."
        )

    print(f"[train_regressor] Loading training data from {data_path}...")
    df = pd.read_csv(data_path)

    feature_cols = [c for c in df.columns if c.startswith("feat_")]
    if len(feature_cols) < 768:
        raise ValueError(f"Expected 768 CROMA features, found {len(feature_cols)} in {data_path}")

    X = df[feature_cols].values.astype(np.float32)
    y = df["sea_ice_concentration"].values.astype(np.float32)

    # 80/20 train/test split with deterministic seed
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    print(f"[train_regressor] Training on {len(X_train)} samples, testing on {len(X_test)} samples...")

    # Pipeline: Standardize -> Compress 768 to 15 components -> L2 Ridge Regression
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=15, random_state=42)),
        ("ridge", Ridge(alpha=100.0, random_state=42))
    ])

    pipeline.fit(X_train, y_train)

    # Evaluate on unseen held-out test split
    y_pred = pipeline.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # Required greppable log format
    print(f"[train_regressor] R2={r2:.4f} MAE={mae:.4f}")

    joblib.dump(pipeline, output_path)
    print(f"[train_regressor] Serialized model to {output_path}")

    return {
        "r2": r2,
        "mae": mae,
        "test_samples": len(X_test),
        "model_path": output_path
    }


if __name__ == "__main__":
    metrics = train_and_save_regressor()
    print(f"Self-healing train completed: R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}")
