# 01_FRONTEND_GEMINI_INSTRUCTIONS.md
## Polaris AI — Frontend Specification (for Gemini Pro / Gemini Code Assist)

You are building the frontend half of Polaris AI, a decision-support console for
Antarctic sea-ice and iceberg navigation (SIH26059, NCPOR/MoES). The backend (built
separately, spec in `02_BACKEND_CLAUDE_INSTRUCTIONS.md`) exposes a FastAPI service on
`http://localhost:8000`. Your job is the entire `/frontend` directory: a Next.js App
Router application in TypeScript, styled with Tailwind CSS, that consumes that backend
and renders a "tactical naval command center" UI.

Do not fabricate any data. Every number, marker position, and route shown in the UI must
come from a real response from the backend. While a request is in flight, show a genuine
loading state — never show a placeholder or last-known-good value dressed up as fresh
data.

---

## 1. Directory Structure (must match exactly)

```
frontend/
├── app/
│   ├── page.tsx               # Main layout & dynamic client loader
│   ├── layout.tsx             # Root layout & global styling
│   └── globals.css            # Tailwind + dark theme custom styling
├── components/
│   ├── MapEngine.tsx          # Leaflet/Mapbox Esri satellite map engine
│   ├── ControlPanel.tsx       # Lat/Lon inputs, drift & weather sliders
│   ├── TelemetryCard.tsx      # Real-time ERA5 & route metrics
│   └── CoverageWidget.tsx     # Real vs. interpolated cell stats
└── package.json               # Node dependencies
```

---

## 2. Tech Stack & Setup

- Next.js (App Router), TypeScript, Tailwind CSS.
- Mapping: React-Leaflet (preferred, lighter weight) or Mapbox GL — either is acceptable,
  but must render the Esri World Imagery satellite basemap.
- No backend calls from Server Components. All API interaction happens client-side from
  `"use client"` components, since the map and live sliders are inherently interactive.
- `package.json` dependencies at minimum: `next`, `react`, `react-dom`, `typescript`,
  `tailwindcss`, `leaflet`, `react-leaflet` (or `mapbox-gl`), `@types/leaflet` if using
  Leaflet.

**Critical SSR Safety Rule:** Leaflet (and most map libraries) touch `window` at import
time, which crashes Next.js SSR/build with `window is not defined`. `MapEngine.tsx` must
therefore be imported into `page.tsx` exclusively via:

```tsx
const MapEngine = dynamic(() => import("@/components/MapEngine"), { ssr: false });
```

Never import `MapEngine` directly (statically) anywhere. Verify this by running
`next build` and confirming zero `window is not defined` errors.

---

## 3. Design Tokens & Theme — "Naval Defense Radar / Dark Mode Console"

Define these as CSS variables in `globals.css` and/or a Tailwind theme extension. Do not
substitute default Tailwind grays/blues for any of these — the exact hex values matter for
visual consistency with the pitch deck.

| Token                  | Hex       | Usage                                   |
|-------------------------|-----------|------------------------------------------|
| Background              | `#0E1117` | Page background, pitch dark              |
| Surface / Cards         | `#1A1E24` | Panel backgrounds, slate                 |
| Accent / Primary        | `#00D2FF` | Polar cyan — buttons, active states, headers |
| Optimized Route Path    | `#00FFCC` | Neon mint — the A* route polyline        |
| Iceberg Markers         | `#FFB300` | Safety amber — iceberg circle markers    |
| Impassable Hazards      | `#FF3B30` | Coral red — high-risk / exclusion zones  |

General styling direction: monospace or technical sans-serif for telemetry numbers,
generous letter-spacing on headers, thin glowing borders on cards (subtle `box-shadow`
using the accent color at low opacity), dark scrollbars. Avoid generic dashboard-template
aesthetics — this should read as a mission-control console, not a SaaS admin panel.

---

## 4. Component Specifications

### 4.1 `app/layout.tsx`
Root layout. Sets `<html lang="en">`, imports `globals.css`, sets the page `<title>` to
something like "Polaris AI — Antarctic Navigation Console", and applies the dark
background token to `<body>`.

### 4.2 `app/page.tsx`
- Client-composed page (can be a Server Component shell that renders client children).
- Layout: a left "Mission Control" column containing `ControlPanel`, and a right/main
  area containing `MapEngine` with `TelemetryCard` and `CoverageWidget` docked as overlay
  panels or a sidebar beneath/beside the map (your call on exact placement — the important
  constraint is that the map dominates the viewport and telemetry is visible without
  scrolling on a standard laptop screen).
- Owns the shared state: `startLat`, `startLon`, `goalLat`, `goalLon`, `hoursOffset`,
  `weatherSeverity`, plus the latest API response (`waypoints`, `metrics`) and a
  `loading`/`error` state.
- Debounce API calls: don't fire a request on every slider pixel — debounce ~300–500ms
  after the user stops dragging, or fire on release. Show a loading indicator on
  `MapEngine`/`TelemetryCard` while a request is in flight.

### 4.3 `components/MapEngine.tsx`
Props: current waypoints, iceberg positions (if returned separately, or derive visual
markers from the metrics/route context), start/goal coordinates, loading state.

Must render:
- Esri World Imagery satellite tile layer as the basemap.
- The Weddell Sea operational bounding box as a polygon/rectangle outline
  (lat -70.0 to -65.0, lon -50.0 to -40.0).
- Iceberg markers in Safety Amber (`#FFB300`).
- A green start marker and a red/distinct destination marker (use the palette's coral red
  `#FF3B30` sparingly here so it doesn't visually collide with hazard-zone semantics —
  consider a distinct marker icon rather than pure color reuse for the destination pin).
- The optimized route as a glowing polyline in Neon Mint (`#00FFCC`) — a CSS `filter:
  drop-shadow(...)` or SVG glow filter on the Leaflet polyline achieves the "glowing"
  effect.
- Re-render the route and marker positions whenever new `waypoints`/metrics arrive from
  the parent — do not memoize away real updates.

### 4.4 `components/ControlPanel.tsx`
Must include:
- Numeric inputs for Departure Latitude/Longitude and Arrival Latitude/Longitude,
  constrained to the operational bounding box (lat -70.0 to -65.0, lon -50.0 to -40.0) with
  inline validation if the user enters something out of range.
- A slider for **Iceberg Drift Forecast Horizon**, range 0–72 (hours), with the current
  value displayed numerically next to the slider.
- A slider for **ERA5 Weather Severity Multiplier**, range 0.5–2.5, step granularity fine
  enough to feel continuous (e.g. 0.1).
- A clear primary "Calculate Safest Route" action if you choose not to auto-trigger on
  every slider change (either auto-trigger with debounce, or an explicit button — pick one
  UX pattern and be consistent; auto-trigger with debounce is preferred to feel "live").
- Visual state for in-flight requests (disable inputs or show a subtle spinner) and for
  errors (e.g. backend unreachable, invalid coordinates) — surface the actual error
  message from the API, not a generic fallback string, when the backend returns one.

### 4.5 `components/TelemetryCard.tsx`
Renders, from the live `metrics` object returned by `POST /api/safest-route`:
- Active ERA5 wind vector: `u10`, `v10`, and computed `speed_ms`.
- Total waypoint count.
- Average route risk score.
- Nothing here should ever be a hardcoded sample value — if `metrics` is null (no
  successful call yet), show an explicit "Awaiting first route calculation" state, not a
  fake number.

### 4.6 `components/CoverageWidget.tsx`
Renders the `grid_coverage` object: `real_cells` vs `interpolated_cells`, ideally as a
simple proportion bar or donut alongside the raw counts, so a user can see at a glance how
much of the current grid is directly observed sea-ice data versus nearest-neighbor
interpolated. Label it clearly — this is a data-honesty feature, not decoration.

---

## 5. API Integration Contract

Base URL: `http://localhost:8000` in development, but **the frontend must ultimately point
at the deployed backend's public URL in production**. Make this an environment variable,
`NEXT_PUBLIC_API_BASE_URL`, set to `http://localhost:8000` in local `.env.local` and to the
real deployed backend domain (e.g. `https://polaris-ai-backend.onrender.com`) in the
hosting platform's environment settings — never hardcode either value directly into
component code.

### `POST /api/safest-route`
Request body:
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

Response body:
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

Handle `status !== "success"` and network failures explicitly with a visible, honest error
state in the UI (e.g. "Route calculation failed — no viable path found" or "Backend
unreachable"), not a silent failure that leaves stale data on screen without indication
that it's stale.

### `GET /api/health-and-audit`
Call this once on initial page load to confirm the backend, models, and datasets are
healthy before allowing the user to submit a route request. If it reports a degraded
state (e.g. model not loaded), surface that clearly in the UI rather than letting the user
submit a request that will fail.

---

## 6. Build & Verification Steps (do these yourself before handing off)

1. `npm install`
2. `npm run dev` — confirm it boots on port 3000 with no console errors.
3. `next build` — confirm a clean production build with **zero** `window is not defined`
   errors (this is the SSR safety rule check).
4. With the backend running on port 8000, load the app, submit a route request, and
   confirm: markers render, the route polyline renders in the correct color, telemetry and
   coverage widgets populate with real numbers, and dragging both sliders produces a new,
   visibly different route/metrics after the debounce window.
5. Confirm the theme tokens above are actually applied (inspect computed styles) — reject
   your own build if default Tailwind slate/blue grays are still visible anywhere they
   should be the specified palette.
6. **Deploy to Vercel (or Netlify)** with `NEXT_PUBLIC_API_BASE_URL` set as a real
   environment variable pointing at the deployed backend. Re-run steps 3–5 against the
   live deployed URL, not just localhost, before considering the frontend finished — a
   local-only success does not satisfy the project requirements.