import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score

# ============================================================
# INITIALIZATION & DATA LOADING (Keep exactly as before)
# ============================================================
DATA_FILE = r"data\training_data.csv"
MODEL_DIR = r"models"
MODEL_FILE = os.path.join(MODEL_DIR, "sea_ice_rf_model.joblib")
os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_FILE)
feature_cols = [c for c in df.columns if c.startswith("feat_")]
X = df[feature_cols].values
y = df["sea_ice_concentration"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ============================================================
# TRAIN OPTIMIZED MODEL (PCA + Ridge)
# ============================================================
print("\nTraining Scaler + PCA + Ridge Pipeline...")
# Standardize features, compress 768 down to 15, apply linear regression with L2 penalty
model = make_pipeline(
    StandardScaler(),
    PCA(n_components=15, random_state=42),
    Ridge(alpha=100.0, random_state=42)
)
model.fit(X_train, y_train)

# ============================================================
# EVALUATE & SAVE (Keep exactly as before)
# ============================================================
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nModel Performance Metrics:")
print(f"- Mean Absolute Error (MAE): {mae:.2f}%")
print(f"- R^2 Score: {r2:.2f}")

joblib.dump(model, MODEL_FILE)
print(f"\nSaved optimized model to: {MODEL_FILE}")