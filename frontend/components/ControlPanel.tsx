"use client";

import React, { useState } from "react";
import { Compass, Sliders, ShieldAlert, Play, RefreshCw, AlertTriangle, Wind } from "lucide-react";

interface ControlPanelProps {
  startLat: number;
  startLon: number;
  goalLat: number;
  goalLon: number;
  hoursOffset: number;
  weatherSeverity: number;
  loading: boolean;
  error: string | null;
  onCoordinatesChange: (coords: {
    startLat?: number;
    startLon?: number;
    goalLat?: number;
    goalLon?: number;
  }) => void;
  onHoursOffsetChange: (val: number) => void;
  onWeatherSeverityChange: (val: number) => void;
  onCalculate: () => void;
}

export default function ControlPanel({
  startLat,
  startLon,
  goalLat,
  goalLon,
  hoursOffset,
  weatherSeverity,
  loading,
  error,
  onCoordinatesChange,
  onHoursOffsetChange,
  onWeatherSeverityChange,
  onCalculate,
}: ControlPanelProps) {
  // Local validation states for inline guidance
  const isStartLatValid = startLat >= -70.0 && startLat <= -65.0;
  const isStartLonValid = startLon >= -50.0 && startLon <= -40.0;
  const isGoalLatValid = goalLat >= -70.0 && goalLat <= -65.0;
  const isGoalLonValid = goalLon >= -50.0 && goalLon <= -40.0;

  const isFormValid =
    isStartLatValid && isStartLonValid && isGoalLatValid && isGoalLonValid;

  return (
    <div className="flex flex-col gap-5 p-5 bg-surface rounded-xl border border-surface-border shadow-tactical text-white">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-accent animate-pulse" />
          <h2 className="text-sm font-mono uppercase tracking-wider font-bold text-accent">
            Mission Control
          </h2>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-background border border-surface-border text-muted">
          SECTOR: WEDDELL
        </span>
      </div>

      {/* Coordinate Inputs */}
      <div className="flex flex-col gap-4">
        {/* Departure Point */}
        <div className="p-3 bg-background/80 rounded-lg border border-surface-border/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-[#00FF88] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00FF88]" />
              DEPARTURE POINT
            </span>
            <span className="text-[10px] font-mono text-muted">[-70°S to -65°S]</span>
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="text-[11px] font-mono text-muted block mb-1">
                Lat (°S)
              </label>
              <input
                type="number"
                step="0.05"
                min="-70.0"
                max="-65.0"
                value={startLat}
                disabled={loading}
                onChange={(e) =>
                  onCoordinatesChange({ startLat: parseFloat(e.target.value) || 0 })
                }
                className={`w-full bg-surface text-sm font-mono px-2.5 py-1.5 rounded border focus:outline-none focus:border-accent transition-colors ${
                  isStartLatValid ? "border-surface-border" : "border-hazard text-hazard"
                }`}
              />
            </div>
            <div>
              <label className="text-[11px] font-mono text-muted block mb-1">
                Lon (°W)
              </label>
              <input
                type="number"
                step="0.05"
                min="-50.0"
                max="-40.0"
                value={startLon}
                disabled={loading}
                onChange={(e) =>
                  onCoordinatesChange({ startLon: parseFloat(e.target.value) || 0 })
                }
                className={`w-full bg-surface text-sm font-mono px-2.5 py-1.5 rounded border focus:outline-none focus:border-accent transition-colors ${
                  isStartLonValid ? "border-surface-border" : "border-hazard text-hazard"
                }`}
              />
            </div>
          </div>
          {(!isStartLatValid || !isStartLonValid) && (
            <p className="text-[10px] font-mono text-hazard mt-1.5 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Coords outside [-70°S, -65°S] or [-50°W, -40°W]
            </p>
          )}
        </div>

        {/* Arrival Destination */}
        <div className="p-3 bg-background/80 rounded-lg border border-surface-border/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-hazard flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-hazard" />
              ARRIVAL DESTINATION
            </span>
            <span className="text-[10px] font-mono text-muted">[-50°W to -40°W]</span>
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="text-[11px] font-mono text-muted block mb-1">
                Lat (°S)
              </label>
              <input
                type="number"
                step="0.05"
                min="-70.0"
                max="-65.0"
                value={goalLat}
                disabled={loading}
                onChange={(e) =>
                  onCoordinatesChange({ goalLat: parseFloat(e.target.value) || 0 })
                }
                className={`w-full bg-surface text-sm font-mono px-2.5 py-1.5 rounded border focus:outline-none focus:border-accent transition-colors ${
                  isGoalLatValid ? "border-surface-border" : "border-hazard text-hazard"
                }`}
              />
            </div>
            <div>
              <label className="text-[11px] font-mono text-muted block mb-1">
                Lon (°W)
              </label>
              <input
                type="number"
                step="0.05"
                min="-50.0"
                max="-40.0"
                value={goalLon}
                disabled={loading}
                onChange={(e) =>
                  onCoordinatesChange({ goalLon: parseFloat(e.target.value) || 0 })
                }
                className={`w-full bg-surface text-sm font-mono px-2.5 py-1.5 rounded border focus:outline-none focus:border-accent transition-colors ${
                  isGoalLonValid ? "border-surface-border" : "border-hazard text-hazard"
                }`}
              />
            </div>
          </div>
          {(!isGoalLatValid || !isGoalLonValid) && (
            <p className="text-[10px] font-mono text-hazard mt-1.5 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Coords outside [-70°S, -65°S] or [-50°W, -40°W]
            </p>
          )}
        </div>
      </div>

      {/* Physics Sliders */}
      <div className="flex flex-col gap-4 pt-1">
        {/* Iceberg Drift Horizon */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-gray-200 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-iceberg" />
              Iceberg Drift Horizon
            </span>
            <span className="font-bold text-iceberg px-2 py-0.5 rounded bg-background border border-surface-border">
              +{hoursOffset} h
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="72"
            step="1"
            value={hoursOffset}
            disabled={loading}
            onChange={(e) => onHoursOffsetChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-background rounded-lg appearance-none cursor-pointer accent-iceberg"
          />
          <div className="flex justify-between text-[10px] font-mono text-muted">
            <span>Now (0h)</span>
            <span>24h</span>
            <span>48h</span>
            <span>72h (Max)</span>
          </div>
        </div>

        {/* ERA5 Weather Severity Multiplier */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-gray-200 flex items-center gap-1.5">
              <Wind className="w-3.5 h-3.5 text-accent" />
              ERA5 Weather Severity
            </span>
            <span className="font-bold text-accent px-2 py-0.5 rounded bg-background border border-surface-border">
              {weatherSeverity.toFixed(1)}x
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.5"
            step="0.1"
            value={weatherSeverity}
            disabled={loading}
            onChange={(e) => onWeatherSeverityChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-background rounded-lg appearance-none cursor-pointer accent-accent"
          />
          <div className="flex justify-between text-[10px] font-mono text-muted">
            <span>0.5x (Calm)</span>
            <span>1.0x (Nominal)</span>
            <span>2.5x (Severe Gale)</span>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={onCalculate}
        disabled={loading || !isFormValid}
        className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-mono text-xs uppercase tracking-wider font-bold transition-all shadow-glow ${
          loading || !isFormValid
            ? "bg-surface-border text-muted cursor-not-allowed border border-transparent"
            : "bg-accent hover:bg-accent-hover text-black cursor-pointer active:scale-[0.98]"
        }`}
      >
        {loading ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin" />
            Recalculating Trajectory...
          </>
        ) : (
          <>
            <Play className="w-4 h-4 fill-current" />
            Calculate Safest Route
          </>
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-3 rounded-lg bg-hazard/10 border border-hazard/40 text-hazard text-xs font-mono flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="block font-bold">Calculation Failed:</strong>
            {error}
          </div>
        </div>
      )}
    </div>
  );
}
