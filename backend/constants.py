"""
Polaris AI - Geographic & Grid Constants
Operational Area: Weddell Sea Sector, Antarctica
"""
from typing import Tuple
import numpy as np

# Geographic boundaries (degrees)
LAT_MAX: float = -65.0   # Northern boundary (65°S)
LAT_MIN: float = -70.0   # Southern boundary (70°S)
LON_MIN: float = -50.0   # Western boundary (50°W)
LON_MAX: float = -40.0   # Eastern boundary (40°W)

# Grid resolution
GRID_SIZE: int = 50      # 50 x 50 spatial grid matrix


def latlon_to_index(lat: float, lon: float) -> Tuple[int, int]:
    """
    Transforms geographic coordinates (GPS lat, lon) to matrix grid indices (r, c).
    Uses round() to prevent IEEE-754 precision truncation mismatches.
    """
    r = int(round((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (GRID_SIZE - 1)))
    c = int(round((lon - LON_MIN) / (LON_MAX - LON_MIN) * (GRID_SIZE - 1)))
    return int(np.clip(r, 0, GRID_SIZE - 1)), int(np.clip(c, 0, GRID_SIZE - 1))


def index_to_latlon(r: int, c: int) -> Tuple[float, float]:
    """
    Inverse transform: converts matrix grid indices (r, c) back to GPS lat, lon.
    """
    lat = float(LAT_MAX - (r / (GRID_SIZE - 1)) * (LAT_MAX - LAT_MIN))
    lon = float(LON_MIN + (c / (GRID_SIZE - 1)) * (LON_MAX - LON_MIN))
    return lat, lon
