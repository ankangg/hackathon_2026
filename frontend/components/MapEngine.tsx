"use client";

import React, { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Rectangle,
  Polyline,
  Marker,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";

interface MapEngineProps {
  waypoints: [number, number][];
  icebergs?: [number, number][];
  startCoords: [number, number];
  goalCoords: [number, number];
  loading: boolean;
}

// Custom tactical SVG div icons for departure and arrival pins
const createCustomPin = (color: string, label: string) => {
  return L.divIcon({
    className: "custom-tactical-pin",
    html: `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%);">
        <div style="background: ${color}; color: #000; font-weight: 800; font-size: 10px; padding: 2px 6px; border-radius: 4px; box-shadow: 0 0 10px ${color}; white-space: nowrap; margin-bottom: 2px; text-transform: uppercase; font-family: monospace;">
          ${label}
        </div>
        <svg width="24" height="32" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 0C5.37258 0 0 5.37258 0 12C0 21 12 32 12 32C12 32 24 21 24 12C24 5.37258 18.6274 0 12 0Z" fill="${color}" filter="drop-shadow(0 0 6px ${color})"/>
          <circle cx="12" cy="12" r="5" fill="#0E1117" />
        </svg>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });
};

// Map View auto-fitter when waypoints or bounds change
function MapAutoFitter({
  waypoints,
  start,
  goal,
}: {
  waypoints: [number, number][];
  start: [number, number];
  goal: [number, number];
}) {
  const map = useMap();

  useEffect(() => {
    if (waypoints && waypoints.length > 0) {
      const bounds = L.latLngBounds([start, goal, ...waypoints]);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    }
  }, [waypoints, start, goal, map]);

  return null;
}

export default function MapEngine({
  waypoints,
  icebergs = [],
  startCoords,
  goalCoords,
  loading,
}: MapEngineProps) {
  // Operational Bounding Box: Weddell Sea Sector (lat -70 to -65, lon -50 to -40)
  const boundingBox: [[number, number], [number, number]] = [
    [-70.0, -50.0],
    [-65.0, -40.0],
  ];

  const startPin = useMemo(() => createCustomPin("#00FF88", "DEPARTURE"), []);
  const goalPin = useMemo(() => createCustomPin("#FF3B30", "ARRIVAL"), []);

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-xl overflow-hidden border border-surface-border bg-background shadow-tactical">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 z-[1000] bg-background/60 backdrop-blur-[2px] flex items-center justify-center pointer-events-none transition-all duration-200">
          <div className="flex flex-col items-center gap-3 p-4 rounded-lg bg-surface/90 border border-accent/40 shadow-glow">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-mono tracking-widest text-accent uppercase font-bold">
              Computing Optimized Path...
            </span>
          </div>
        </div>
      )}

      <MapContainer
        center={[-67.5, -45.0]}
        zoom={6}
        minZoom={4}
        maxZoom={12}
        className="w-full h-full"
        zoomControl={true}
      >
        {/* Esri World Imagery Satellite Tiles */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community"
          maxZoom={12}
        />

        {/* Weddell Sea Operational Bounding Box */}
        <Rectangle
          bounds={boundingBox}
          pathOptions={{
            color: "#00D2FF",
            weight: 2,
            dashArray: "6, 6",
            fill: false,
          }}
        >
          <Popup className="tactical-popup">
            <div className="text-xs font-mono p-1">
              <strong className="text-accent">Weddell Sea Operational Grid</strong>
              <div className="text-gray-300">Lat: 65°S to 70°S | Lon: 40°W to 50°W</div>
            </div>
          </Popup>
        </Rectangle>

        {/* Drifted Iceberg Threat Markers (Safety Amber #FFB300) */}
        {icebergs.map(([lat, lon], idx) => (
          <CircleMarker
            key={`iceberg-${idx}-${lat}-${lon}`}
            center={[lat, lon]}
            radius={8}
            pathOptions={{
              color: "#FFB300",
              fillColor: "#FFB300",
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-xs font-mono p-1 text-surface">
                <span className="font-bold text-[#D97706]">⚠️ Tracked Iceberg Core</span>
                <div>Position: {lat.toFixed(3)}°S, {lon.toFixed(3)}°W</div>
                <div className="text-red-600 font-bold">Risk Score: 100 (Exclusion Zone)</div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Start / Departure Marker */}
        <Marker position={startCoords} icon={startPin}>
          <Popup>
            <div className="text-xs font-mono p-1 text-surface">
              <strong className="text-emerald-700">Planned Departure</strong>
              <div>Lat: {startCoords[0].toFixed(2)}°S</div>
              <div>Lon: {startCoords[1].toFixed(2)}°W</div>
            </div>
          </Popup>
        </Marker>

        {/* Goal / Destination Marker */}
        <Marker position={goalCoords} icon={goalPin}>
          <Popup>
            <div className="text-xs font-mono p-1 text-surface">
              <strong className="text-red-600">Planned Destination</strong>
              <div>Lat: {goalCoords[0].toFixed(2)}°S</div>
              <div>Lon: {goalCoords[1].toFixed(2)}°W</div>
            </div>
          </Popup>
        </Marker>

        {/* A* Optimized Route Polyline in Neon Mint (#00FFCC) with Glowing Effect */}
        {waypoints.length > 0 && (
          <>
            {/* Glow underlay */}
            <Polyline
              positions={waypoints}
              pathOptions={{
                color: "#00FFCC",
                weight: 8,
                opacity: 0.35,
                lineCap: "round",
                lineJoin: "round",
              }}
            />
            {/* Crisp core path */}
            <Polyline
              positions={waypoints}
              pathOptions={{
                color: "#00FFCC",
                weight: 3.5,
                opacity: 0.95,
                lineCap: "round",
                lineJoin: "round",
                className: "glowing-route",
              }}
            >
              <Popup>
                <div className="text-xs font-mono p-1 text-surface">
                  <strong className="text-[#00BFA5]">A* ML-Optimized Safe Trajectory</strong>
                  <div>Waypoints: {waypoints.length}</div>
                  <div>Status: Path Verified Safe (Risk &lt; 95)</div>
                </div>
              </Popup>
            </Polyline>
          </>
        )}

        <MapAutoFitter waypoints={waypoints} start={startCoords} goal={goalCoords} />
      </MapContainer>
    </div>
  );
}
