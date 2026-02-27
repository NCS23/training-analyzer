import { useEffect, useRef, useCallback } from 'react';
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
  /** Called when user hovers on route. pointIndex into GPSPoint[], or null. */
  onHoverPoint?: (pointIndex: number | null) => void;
  /** Display mode: plain route, pace heat map, or HR heat map. */
  mode?: HeatMapMode;
  /** Colored segments for pace/hr modes. */
  segments?: RouteSegment[];
}

/** Format pace as M:SS string. */
function formatPace(paceMinPerKm: number): string {
  const mins = Math.floor(paceMinPerKm);
  const secs = Math.round((paceMinPerKm - mins) * 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/** Calculate pace for a point, with haversine fallback from neighbors. */
function getPointPace(points: GPSPoint[], idx: number): number | null {
  const p = points[idx];
  if (p.speed != null && p.speed > 0) {
    const pace = 1000 / p.speed / 60;
    return pace > 1 && pace < 30 ? pace : null;
  }
  if (idx === 0) return null;
  const prev = points[idx - 1];
  const dt = p.seconds - prev.seconds;
  if (dt <= 0) return null;
  const R = 6371000;
  const dLat = ((p.lat - prev.lat) * Math.PI) / 180;
  const dLng = ((p.lng - prev.lng) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((prev.lat * Math.PI) / 180) * Math.cos((p.lat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  if (dist < 0.1 || dist > 500) return null;
  const pace = 1000 / (dist / dt) / 60;
  return pace > 1 && pace < 30 ? pace : null;
}

/** Build tooltip HTML for a GPS point, adapted to the current map mode. */
function buildPointTooltip(points: GPSPoint[], idx: number, distKm: number, mode: HeatMapMode): string {
  const p = points[idx];
  const dist = `${distKm.toFixed(2)} km`;
  const pace = getPointPace(points, idx);

  if (mode === 'pace') {
    if (pace != null) return `<b>${formatPace(pace)} /km</b><br>${dist}`;
    return dist;
  }

  if (mode === 'hr') {
    if (p.hr != null) return `<b>${p.hr} bpm</b><br>${dist}`;
    return dist;
  }

  // Route mode: altitude + distance only
  if (p.alt != null) return `<b>${Math.round(p.alt)} m</b><br>${dist}`;
  return dist;
}

export function RouteMap({
  points,
  height = '300px',
  className = '',
  darkMode = false,
  hoveredPointIndex,
  onHoverPoint,
  mode = 'route',
  segments,
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const hoverMarkerRef = useRef<L.CircleMarker | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | null>(null);
  const onHoverPointRef = useRef(onHoverPoint);
  onHoverPointRef.current = onHoverPoint;
  const modeRef = useRef(mode);
  modeRef.current = mode;

  // Pre-compute cumulative distances for tooltip display
  const cumulativeDistKm = useRef<number[]>([]);

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

  // Find nearest GPS point index to a map latlng
  const findNearestPointIndex = useCallback(
    (latlng: L.LatLng): number | null => {
      if (points.length === 0) return null;
      const map = mapRef.current;
      if (!map) return null;

      const mousePoint = map.latLngToContainerPoint(latlng);
      let bestIdx = 0;
      let bestDist = Infinity;

      // Sample every 3rd point for performance on large tracks
      const step = points.length > 1000 ? 3 : 1;
      for (let i = 0; i < points.length; i += step) {
        const pt = map.latLngToContainerPoint([points[i].lat, points[i].lng]);
        const dx = pt.x - mousePoint.x;
        const dy = pt.y - mousePoint.y;
        const d = dx * dx + dy * dy;
        if (d < bestDist) {
          bestDist = d;
          bestIdx = i;
        }
      }

      // Only match if within 30px
      return bestDist < 900 ? bestIdx : null;
    },
    [points],
  );

  // Pre-compute cumulative distances
  useEffect(() => {
    const dists = [0];
    let cumDist = 0;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const R = 6371000;
      const dLat = ((curr.lat - prev.lat) * Math.PI) / 180;
      const dLng = ((curr.lng - prev.lng) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos((prev.lat * Math.PI) / 180) *
          Math.cos((curr.lat * Math.PI) / 180) *
          Math.sin(dLng / 2) ** 2;
      const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      cumDist += dist < 500 ? dist : 0;
      dists.push(cumDist / 1000);
    }
    cumulativeDistKm.current = dists;
  }, [points]);

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

    // Invisible wide polyline for easy mouse interaction
    const hitArea = L.polyline(positions, {
      color: 'transparent',
      weight: 40,
      opacity: 0,
      interactive: true,
    }).addTo(layerGroup);

    hitArea.on('mousemove', (e: L.LeafletMouseEvent) => {
      const idx = findNearestPointIndex(e.latlng);
      if (idx != null) {
        onHoverPointRef.current?.(idx);
        // Show tooltip on hover marker
        const distKm = cumulativeDistKm.current[idx] ?? 0;
        const tooltipHtml = buildPointTooltip(points, idx, distKm, modeRef.current);
        if (hoverMarkerRef.current) {
          hoverMarkerRef.current
            .unbindTooltip()
            .bindTooltip(tooltipHtml, {
              permanent: true,
              direction: 'top',
              offset: [0, -10],
              className: 'route-hover-tooltip',
            })
            .openTooltip();
        }
      }
    });

    hitArea.on('mouseout', () => {
      onHoverPointRef.current?.(null);
      if (hoverMarkerRef.current) {
        hoverMarkerRef.current.unbindTooltip();
      }
    });

    if (mode !== 'route' && segments && segments.length > 0) {
      // Heat map: colored segments
      for (const seg of segments) {
        const polyline = L.polyline(seg.positions, {
          color: seg.color,
          weight: 4,
          opacity: 0.9,
          interactive: false,
        });
        layerGroup.addLayer(polyline);
      }
    } else {
      // Default: single blue line
      L.polyline(positions, {
        color: '#3b82f6',
        weight: 3,
        opacity: 0.85,
        interactive: false,
      }).addTo(layerGroup);
    }
  }, [mode, segments, positions.length, findNearestPointIndex, points]); // eslint-disable-line react-hooks/exhaustive-deps

  // Hover marker (separate effect to avoid map re-init)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (hoveredPointIndex == null || !points[hoveredPointIndex]) {
      // Remove marker when not hovering
      if (hoverMarkerRef.current) {
        hoverMarkerRef.current.unbindTooltip();
        hoverMarkerRef.current.remove();
        hoverMarkerRef.current = null;
      }
      return;
    }

    const p = points[hoveredPointIndex];
    const latlng = L.latLng(p.lat, p.lng);
    const distKm = cumulativeDistKm.current[hoveredPointIndex] ?? 0;
    const tooltipHtml = buildPointTooltip(points, hoveredPointIndex, distKm, mode);

    if (hoverMarkerRef.current) {
      hoverMarkerRef.current.setLatLng(latlng);
      hoverMarkerRef.current
        .unbindTooltip()
        .bindTooltip(tooltipHtml, {
          permanent: true,
          direction: 'top',
          offset: [0, -10],
          className: 'route-hover-tooltip',
        })
        .openTooltip();
    } else {
      hoverMarkerRef.current = L.circleMarker(latlng, {
        radius: 6,
        color: '#fff',
        weight: 2,
        fillColor: '#3b82f6',
        fillOpacity: 1,
        interactive: false,
      }).addTo(map);
      hoverMarkerRef.current
        .bindTooltip(tooltipHtml, {
          permanent: true,
          direction: 'top',
          offset: [0, -10],
          className: 'route-hover-tooltip',
        })
        .openTooltip();
    }
  }, [hoveredPointIndex, points, mode]);

  if (positions.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className={`isolate rounded-[var(--radius-component-md)] overflow-hidden border border-[var(--color-border-default)] ${className}`}
      style={{ height }}
    />
  );
}
