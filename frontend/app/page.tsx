"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import ControlPanel from "@/components/ControlPanel";
import TelemetryCard from "@/components/TelemetryCard";
import CoverageWidget from "@/components/CoverageWidget";
import { ShieldCheck, AlertTriangle, Radio, Anchor, Terminal } from "lucide-react";

// Critical SSR Safety Rule: Leaflet touches window at import time.
// MapEngine must ONLY be imported dynamically with { ssr: false }.
const MapEngine = dynamic(() => import("@/components/MapEngine"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] rounded-xl border border-surface-border bg-surface flex flex-col items-center justify-center gap-3">
      <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      <span className="text-xs font-mono uppercase tracking-widest text-accent">
        Loading Tactical Satellite Engine...
      </span>
    </div>
  ),
});

interface HealthStatus {
  status: string;
  models?: {
    croma_loaded?: boolean;
    regressor_loaded?: boolean;
  };
  grid_coverage?: {
    real_cells: number;
    interpolated_cells: number;
  };
}

export default function Home() {
  // Shared Mission State (Default within Weddell Sea bounding box)
  const [startLat, setStartLat] = useState<number>(-65.2);
  const [startLon, setStartLon] = useState<number>(-49.5);
  const [goalLat, setGoalLat] = useState<number>(-69.8);
  const [goalLon, setGoalLon] = useState<number>(-40.5);
  const [hoursOffset, setHoursOffset] = useState<number>(24);
  const [weatherSeverity, setWeatherSeverity] = useState<number>(1.2);

  // Response state
  const [waypoints, setWaypoints] = useState<[number, number][]>([]);
  const [icebergs, setIcebergs] = useState<[number, number][]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Health and audit pre-flight state
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [backendDegraded, setBackendDegraded] = useState<string | null>(null);

  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  // Pre-flight health check on page load
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch(`${API_BASE}/api/health-and-audit`, {
          headers: {
            "Bypass-Tunnel-Reminder": "true",
          },
        });
        if (!res.ok) {
          throw new Error(`Health audit check returned status ${res.status}`);
        }
        const data: HealthStatus = await res.json();
        setHealth(data);

        if (data.status === "degraded") {
          setBackendDegraded(
            "Backend reporting degraded models or incomplete spatial grid."
          );
        } else {
          setBackendDegraded(null);
        }
      } catch (err: any) {
        console.warn("[Polaris Console] Initial health check warning:", err.message);
        setBackendDegraded(
          `Unable to connect to backend at ${API_BASE}. Ensure FastAPI service is running.`
        );
      }
    }
    checkHealth();
  }, [API_BASE]);

  // Main Safe-Route API fetch routine
  const fetchSafestRoute = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/safest-route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Bypass-Tunnel-Reminder": "true",
        },
        body: JSON.stringify({
          start_lat: startLat,
          start_lon: startLon,
          goal_lat: goalLat,
          goal_lon: goalLon,
          hours_offset: hoursOffset,
          weather_severity: weatherSeverity,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(
          errData.detail ||
            errData.message ||
            `HTTP ${res.status}: Failed to calculate safe route`
        );
      }

      const data = await res.json();

      if (data.status !== "success") {
        setError(data.message || "Route calculation failed: goal unreachable.");
        setWaypoints([]);
      } else {
        setWaypoints(data.waypoints || []);
        if (data.icebergs) {
          setIcebergs(data.icebergs);
        }
        setMetrics(data.metrics || null);
        setError(null);
      }
    } catch (err: any) {
      setError(
        err.message ||
          "Backend unreachable. Please verify the navigation service is online."
      );
      setWaypoints([]);
    } finally {
      setLoading(false);
    }
  }, [API_BASE, startLat, startLon, goalLat, goalLon, hoursOffset, weatherSeverity]);

  // Auto-trigger calculation initially and on debounced slider changes (350ms)
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      fetchSafestRoute();
    }, 350);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [hoursOffset, weatherSeverity, fetchSafestRoute]);

  const handleCoordinatesChange = (coords: {
    startLat?: number;
    startLon?: number;
    goalLat?: number;
    goalLon?: number;
  }) => {
    if (coords.startLat !== undefined) setStartLat(coords.startLat);
    if (coords.startLon !== undefined) setStartLon(coords.startLon);
    if (coords.goalLat !== undefined) setGoalLat(coords.goalLat);
    if (coords.goalLon !== undefined) setGoalLon(coords.goalLon);
  };

  return (
    <main className="min-h-screen bg-background text-white flex flex-col">
      {/* Top Tactical Command Bar */}
      <header className="border-b border-surface-border bg-surface/90 px-5 py-3 backdrop-blur sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/40 flex items-center justify-center text-accent">
            <Anchor className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-mono font-bold tracking-wider text-accent uppercase">
                Polaris AI
              </h1>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-border text-gray-300 font-semibold">
                SIH26059 / NCPOR
              </span>
            </div>
            <p className="text-[11px] text-muted font-sans">
              Antarctic Sea-Ice & Iceberg Maritime Decision Support Console
            </p>
          </div>
        </div>

        {/* System Health Indicator */}
        <div className="flex items-center gap-3 font-mono text-xs">
          {backendDegraded ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-hazard/10 border border-hazard/40 text-hazard">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Degraded Connection</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/40 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Naval Radar Online</span>
            </div>
          )}

          <div className="flex items-center gap-1 text-muted text-[11px] hidden md:flex">
            <Radio className="w-3 h-3 text-accent animate-pulse" />
            <span>CROMA ViT / ERA5 Reanalysis</span>
          </div>
        </div>
      </header>

      {/* Main Console Viewport */}
      <div className="flex-1 p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-5 max-w-[1920px] w-full mx-auto">
        {/* Left Column: Mission Parameters Control Panel (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <ControlPanel
            startLat={startLat}
            startLon={startLon}
            goalLat={goalLat}
            goalLon={goalLon}
            hoursOffset={hoursOffset}
            weatherSeverity={weatherSeverity}
            loading={loading}
            error={error}
            onCoordinatesChange={handleCoordinatesChange}
            onHoursOffsetChange={setHoursOffset}
            onWeatherSeverityChange={setWeatherSeverity}
            onCalculate={fetchSafestRoute}
          />

          {/* Docked Provenance Widget under control panel on desktop */}
          <div className="hidden lg:block">
            <CoverageWidget coverage={metrics?.grid_coverage || health?.grid_coverage} />
          </div>
        </div>

        {/* Right Column: Tactical Map Engine + Live Telemetry (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4 min-h-[600px]">
          {/* Map Dominates Viewport */}
          <div className="flex-1 min-h-[480px] lg:min-h-[560px]">
            <MapEngine
              waypoints={waypoints}
              icebergs={icebergs}
              startCoords={[startLat, startLon]}
              goalCoords={[goalLat, goalLon]}
              loading={loading}
            />
          </div>

          {/* Telemetry & Provenance Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-1 gap-4">
            <TelemetryCard metrics={metrics} loading={loading} />
          </div>

          {/* Visible on Mobile / Narrow screens under telemetry */}
          <div className="block lg:hidden">
            <CoverageWidget coverage={metrics?.grid_coverage || health?.grid_coverage} />
          </div>
        </div>
      </div>
    </main>
  );
}
