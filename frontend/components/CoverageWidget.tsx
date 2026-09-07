"use client";

import React from "react";
import { Database, CheckCircle2, Shuffle } from "lucide-react";

interface CoverageWidgetProps {
  coverage?: {
    real_cells: number;
    interpolated_cells: number;
  };
}

export default function CoverageWidget({ coverage }: CoverageWidgetProps) {
  if (!coverage) {
    return (
      <div className="p-4 bg-surface rounded-xl border border-surface-border shadow-tactical text-xs font-mono text-muted text-center">
        Data provenance will appear on route sync.
      </div>
    );
  }

  const { real_cells, interpolated_cells } = coverage;
  const total = real_cells + interpolated_cells || 2500;
  const realPct = Math.round((real_cells / total) * 100);
  const interpPct = 100 - realPct;

  return (
    <div className="p-4 bg-surface rounded-xl border border-surface-border shadow-tactical text-white">
      {/* Title & Data-Honesty Header */}
      <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-accent">
            Grid Coverage & Provenance
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-background border border-surface-border text-muted">
          50x50 MATRIX (2500 CELLS)
        </span>
      </div>

      <p className="text-[11px] font-sans text-gray-300 leading-normal mb-3">
        <strong className="text-accent font-mono">Data-Honesty Disclosure:</strong> Distinguishes
        direct satellite observations from spatial nearest-neighbor interpolated cells.
      </p>

      {/* Visual Proportion Bar */}
      <div className="w-full h-3 bg-background rounded-full overflow-hidden flex border border-surface-border/80 mb-3">
        <div
          style={{ width: `${realPct}%` }}
          className="h-full bg-accent transition-all duration-500 shadow-glow"
          title={`Direct Observed: ${realPct}%`}
        />
        <div
          style={{ width: `${interpPct}%` }}
          className="h-full bg-surface-border transition-all duration-500"
          title={`Interpolated: ${interpPct}%`}
        />
      </div>

      {/* Numeric Breakdown */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 bg-background rounded-lg border border-accent/20 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-accent text-[11px] font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Direct Observed
          </div>
          <div className="mt-1">
            <span className="text-base font-bold text-white">{real_cells}</span>
            <span className="text-[10px] text-muted ml-1">cells ({realPct}%)</span>
          </div>
          <span className="text-[9px] text-muted mt-0.5">Sentinel-1 + NOAA</span>
        </div>

        <div className="p-2.5 bg-background rounded-lg border border-surface-border flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-gray-300 text-[11px] font-bold">
            <Shuffle className="w-3.5 h-3.5 text-muted" />
            Interpolated
          </div>
          <div className="mt-1">
            <span className="text-base font-bold text-white">{interpolated_cells}</span>
            <span className="text-[10px] text-muted ml-1">cells ({interpPct}%)</span>
          </div>
          <span className="text-[9px] text-muted mt-0.5">Nearest-Neighbor</span>
        </div>
      </div>
    </div>
  );
}
