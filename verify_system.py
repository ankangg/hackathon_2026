import requests
import json
import numpy as np

BASE_URL = 'http://localhost:8000'

print('=' * 65)
print('POLARIS AI AUTOMATED VERIFICATION SUITE')
print('=' * 65)

# 1. Health and Audit Check
res = requests.get(f'{BASE_URL}/api/health-and-audit')
print(f'1. GET /api/health-and-audit: HTTP {res.status_code}')
audit = res.json()
print(json.dumps(audit, indent=2))
assert audit['status'] == 'healthy'
assert audit['models']['croma_loaded'] is True
assert audit['models']['regressor_loaded'] is True
assert audit['assets']['era5'] is True
assert audit['assets']['sic_ground_truth'] is True
assert audit['assets']['iceberg_tracks'] is True
assert audit['assets']['sic_grid'] is True
print('>>> Audit Verification PASSED!\n')

# 2. Forecast Horizon Sweep (0h, 12h, 24h, 48h, 72h)
print('2. FORECAST HORIZON DYNAMIC DRIFT SWEEP:')
horizon_results = []
for h in [0, 12, 24, 48, 72]:
    payload = {
        'start_lat': -65.2,
        'start_lon': -49.5,
        'goal_lat': -69.8,
        'goal_lon': -40.5,
        'hours_offset': float(h),
        'weather_severity': 1.2
    }
    r = requests.post(f'{BASE_URL}/api/safest-route', json=payload)
    data = r.json()
    first_ib = data['icebergs'][0] if data.get('icebergs') else None
    wind = data['metrics']['wind_vector']
    avg_risk = data['metrics']['average_risk']
    wps = data['metrics']['total_waypoints']
    horizon_results.append((h, first_ib, wind, avg_risk, wps))
    print(f'Horizon +{h:02d}h -> Iceberg[0]: {first_ib} | Wind: speed={wind["speed_ms"]} m/s (u10={wind["u10"]}, v10={wind["v10"]}) | Avg Risk: {avg_risk} | Waypoints: {wps}')

ib_lat_0 = horizon_results[0][1][0]
ib_lat_72 = horizon_results[-1][1][0]
print(f'Iceberg Latitude drift: {ib_lat_0} -> {ib_lat_72}')
assert ib_lat_0 != ib_lat_72, 'Iceberg drift must change dynamically with forecast horizon!'
print('>>> Dynamic Drift Verification PASSED!\n')

# 3. Weather Severity Multiplier Sweep (0.5x, 1.0x, 1.5x, 2.0x, 2.5x)
print('3. WEATHER SEVERITY MULTIPLIER SWEEP:')
weather_results = []
for w in [0.5, 1.0, 1.5, 2.0, 2.5]:
    payload = {
        'start_lat': -65.2,
        'start_lon': -49.5,
        'goal_lat': -69.8,
        'goal_lon': -40.5,
        'hours_offset': 24.0,
        'weather_severity': float(w)
    }
    r = requests.post(f'{BASE_URL}/api/safest-route', json=payload)
    data = r.json()
    wind = data['metrics']['wind_vector']
    avg_risk = data['metrics']['average_risk']
    wps = data['metrics']['total_waypoints']
    weather_results.append((w, wind, avg_risk, wps))
    print(f'Severity {w:.1f}x -> Wind speed: {wind["speed_ms"]} m/s | Avg Risk: {avg_risk} | Waypoints: {wps}')

assert weather_results[0][2] < weather_results[-1][2], 'Risk must scale with weather severity!'
print('>>> Weather Scaling Verification PASSED!\n')

# 4. Strict Safety Barrier Verification (Risk >= 95)
print('4. SAFETY BARRIER & EXCLUSION ZONE REJECTION:')
payload_obs = {
    'start_lat': -65.2,
    'start_lon': -49.5,
    'goal_lat': -68.99,
    'goal_lon': -45.55, # Target actual tracked iceberg 0 exclusion core
    'hours_offset': 0.0,
    'weather_severity': 1.2
}
r_obs = requests.post(f'{BASE_URL}/api/safest-route', json=payload_obs)
data_obs = r_obs.json()
print('Direct Obstacle Target Response Status:', data_obs.get('status'))
print('Direct Obstacle Message:', data_obs.get('message'))
assert data_obs['status'] == 'failed', 'Direct route to obstacle must be rejected!'
print('>>> Safety Barrier Rejection PASSED!\n')

print('=' * 65)
print('ALL AUTOMATED VERIFICATIONS COMPLETED AND VERIFIED 100% CLEAN')
print('=' * 65)
