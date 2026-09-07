"use client";

import React from "react";
import { Activity, Wind, Navigation, AlertOctagon, Clock } from "lucide-react";

interface WindVectorData {
  u10: number;
  v10: number;
  speed_ms: number;
}

interface TelemetryMetrics {
  total_waypoints: number;
  wind_vector: WindVectorData;
  average_risk: number;
  grid_coverage?: {
    real_cells: number;
    interpolated_cells: number;
  };
}

interface TelemetryCardProps {
  metrics: TelemetryMetrics | null;
  loading: boolean;
}

export default function TelemetryCard({ metrics, loading }: TelemetryCardProps) {
  if (loading) {
    return (
      <div className="p-4 bg-surface rounded-xl border border-surface-border shadow-tactical animate-pulse">
        <div className="h-4 w-36 bg-surface-border rounded mb-3" />
        <div className="grid grid-cols-3 gap-3">
          <div className="h-16 bg-surface-border rounded" />
          <div className="h-16 bg-surface-border rounded" />
          <div className="h-16 bg-surface-border rounded" />
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-4 bg-surface rounded-xl border border-surface-border shadow-tactical flex items-center justify-center gap-2 text-xs font-mono text-muted py-6">
        <Clock className="w-4 h-4 text-accent animate-spin" />
        <span>Awaiting first route calculation...</span>
      </div>
    );
  }

  const { total_waypoints, wind_vector, average_risk } = metrics;

  return (
    <div className="p-4 bg-surface rounded-xl border border-surface-border shadow-tactical text-white">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-accent">
            Live Route Telemetry
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-background text-emerald-400 border border-emerald-500/30">
          ONLINE / SYNCED
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
        {/* Active Wind Vector */}
        <div className="p-2.5 bg-background rounded-lg border border-surface-border/80 flex flex-col justify-between">
          <span className="text-[10px] text-muted uppercase flex items-center gap-1">
            <Wind className="w-3 h-3 text-accent" />
            ERA5 Wind Vector
          </span>
          <div className="mt-1">
            <div className="text-base font-bold text-accent">
              {wind_vector.speed_ms.toFixed(2)}{" "}
              <span className="text-[10px] text-muted font-normal">m/s</span>
            </div>
            <div className="text-[10px] text-muted">
              u10: <span className="text-white">{wind_vector.u10.toFixed(2)}</span> | v10:{" "}
              <span className="text-white">{wind_vector.v10.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Total Waypoints */}
        <div className="p-2.5 bg-background rounded-lg border border-surface-border/80 flex flex-col justify-between">
          <span className="text-[10px] text-muted uppercase flex items-center gap-1">
            <Navigation className="w-3 h-3 text-route" />
            Waypoints Count
          </span>
          <div className="mt-1">
            <div className="text-base font-bold text-route">
              {total_waypoints}
            </div>
            <div className="text-[10px] text-muted">A* Navigational Nodes</div>
          </div>
        </div>

        {/* Average Route Risk Score */}
        <div className="p-2.5 bg-background rounded-lg border border-surface-border/80 flex flex-col justify-between">
          <span className="text-[10px] text-muted uppercase flex items-center gap-1">
            <AlertOctagon className="w-3 h-3 text-amber-400" />
            Mean Risk Score
          </span>
          <div className="mt-1">
            <div className="text-base font-bold text-amber-400">
              {average_risk.toFixed(1)}{" "}
              <span className="text-[10px] text-muted font-normal">/ 100</span>
            </div>
            <div className="text-[10px] text-muted">
              Threshold: &lt; 95 (Safe Passage)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
