import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GPSPoint } from '@/api/training';

/* ------------------------------------------------------------------ */
/*  Tile config                                                        */
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
/*  RouteMap — plain Leaflet, no react-leaflet wrapper                 */
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
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  const positions: L.LatLngTuple[] = points.map((p) => [p.lat, p.lng]);

  useEffect(() => {
    if (!containerRef.current || positions.length === 0) return;

    // Prevent double-init in StrictMode
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const map = L.map(containerRef.current, {
      scrollWheelZoom: true,
    });
    mapRef.current = map;

    const tile = darkMode ? TILES.dark : TILES.light;
    L.tileLayer(tile.url, { attribution: tile.attribution }).addTo(map);

    L.polyline(positions, {
      color: '#3b82f6',
      weight: 3,
      opacity: 0.85,
    }).addTo(map);

    map.fitBounds(L.latLngBounds(positions), { padding: [30, 30] });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [positions.length, darkMode]); // eslint-disable-line react-hooks/exhaustive-deps

  if (positions.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className={`isolate rounded-[var(--radius-component-md)] overflow-hidden border border-[var(--color-border-default)] ${className}`}
      style={{ height }}
    />
  );
}
