import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, useMap } from 'react-leaflet';
import type { LatLngBoundsExpression, LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GPSPoint } from '@/api/training';

/* ------------------------------------------------------------------ */
/*  Tile Layers                                                        */
/* ------------------------------------------------------------------ */

const TILES = {
  light: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
  },
} as const;

/* ------------------------------------------------------------------ */
/*  Auto-fit bounds                                                    */
/* ------------------------------------------------------------------ */

function FitBounds({ positions }: { positions: LatLngTuple[] }) {
  const map = useMap();
  const fitted = useRef(false);

  useEffect(() => {
    if (positions.length > 0 && !fitted.current) {
      const bounds: LatLngBoundsExpression = positions;
      map.fitBounds(bounds, { padding: [30, 30] });
      fitted.current = true;
    }
  }, [map, positions]);

  return null;
}

/* ------------------------------------------------------------------ */
/*  RouteMap                                                           */
/* ------------------------------------------------------------------ */

export interface RouteMapProps {
  points: GPSPoint[];
  height?: string;
  className?: string;
  darkMode?: boolean;
}

export function RouteMap({
  points,
  height = '300px',
  className = '',
  darkMode = false,
}: RouteMapProps) {
  const positions: LatLngTuple[] = points.map((p) => [p.lat, p.lng]);

  if (positions.length === 0) return null;

  const center = positions[Math.floor(positions.length / 2)];
  const tile = darkMode ? TILES.dark : TILES.light;

  return (
    <div
      className={`rounded-[var(--radius-component-md)] overflow-hidden border border-[var(--color-border-default)] ${className}`}
      style={{ height }}
    >
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url={tile.url} attribution={tile.attribution} />
        <Polyline
          positions={positions}
          pathOptions={{
            color: 'var(--color-interactive-primary, #3b82f6)',
            weight: 3,
            opacity: 0.85,
          }}
        />
        <FitBounds positions={positions} />
      </MapContainer>
    </div>
  );
}
