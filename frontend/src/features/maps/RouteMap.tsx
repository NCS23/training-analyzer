import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GPSPoint } from '@/api/training';
import type { RouteSegment } from '@/utils/segmentBuilder';
import type { HeatMapMode } from '@/utils/colorScale';

/* ------------------------------------------------------------------ */
/*  Tile config                                                        */
/* ------------------------------------------------------------------ */

const TILES = {
  light: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
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
  /** Index of point to highlight with a marker (for chart sync). */
  hoveredPointIndex?: number | null;
  /** Display mode: plain route, pace heat map, or HR heat map. */
  mode?: HeatMapMode;
  /** Colored segments for pace/hr modes. */
  segments?: RouteSegment[];
}

export function RouteMap({
  points,
  height = '300px',
  className = '',
  darkMode = false,
  hoveredPointIndex,
  mode = 'route',
  segments,
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const hoverMarkerRef = useRef<L.CircleMarker | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | null>(null);

  const positions: L.LatLngTuple[] = points.map((p) => [p.lat, p.lng]);

  // Map initialization (only tiles + bounds, no route drawing)
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

    map.fitBounds(L.latLngBounds(positions), { padding: [30, 30] });

    return () => {
      hoverMarkerRef.current = null;
      routeLayerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, [positions.length, darkMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // Route rendering (separate effect — reacts to mode/segments changes)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || positions.length === 0) return;

    // Remove previous route layer
    if (routeLayerRef.current) {
      routeLayerRef.current.remove();
      routeLayerRef.current = null;
    }

    const layerGroup = L.layerGroup().addTo(map);
    routeLayerRef.current = layerGroup;

    if (mode !== 'route' && segments && segments.length > 0) {
      // Heat map: colored segments
      for (const seg of segments) {
        const polyline = L.polyline(seg.positions, {
          color: seg.color,
          weight: 4,
          opacity: 0.9,
        });
        polyline.bindTooltip(seg.label, { sticky: true, direction: 'top', offset: [0, -8] });
        layerGroup.addLayer(polyline);
      }
    } else {
      // Default: single blue line
      L.polyline(positions, {
        color: '#3b82f6',
        weight: 3,
        opacity: 0.85,
      }).addTo(layerGroup);
    }
  }, [mode, segments, positions.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // Hover marker (separate effect to avoid map re-init)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (hoveredPointIndex == null || !points[hoveredPointIndex]) {
      // Remove marker when not hovering
      if (hoverMarkerRef.current) {
        hoverMarkerRef.current.remove();
        hoverMarkerRef.current = null;
      }
      return;
    }

    const p = points[hoveredPointIndex];
    const latlng = L.latLng(p.lat, p.lng);

    if (hoverMarkerRef.current) {
      hoverMarkerRef.current.setLatLng(latlng);
    } else {
      hoverMarkerRef.current = L.circleMarker(latlng, {
        radius: 6,
        color: '#fff',
        weight: 2,
        fillColor: '#3b82f6',
        fillOpacity: 1,
      }).addTo(map);
    }
  }, [hoveredPointIndex, points]);

  if (positions.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className={`isolate rounded-[var(--radius-component-md)] overflow-hidden border border-[var(--color-border-default)] ${className}`}
      style={{ height }}
    />
  );
}
