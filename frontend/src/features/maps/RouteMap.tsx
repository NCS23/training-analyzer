import { useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GPSPoint } from '@/api/training';
import type { RouteSegment } from '@/utils/segmentBuilder';
import type { HeatMapMode } from '@/utils/colorScale';
import type { KmMarkerData, LapMarkerData } from '@/utils/mapMarkers';
import { buildKmPopupHtml, buildLapPopupHtml, LAP_TYPE_COLORS, LAP_TYPE_DASHED } from '@/utils/mapMarkers';
import type { MapTileStyle } from './tileStyles';
import { TILES } from './tileStyles';

/* ------------------------------------------------------------------ */
/*  RouteMap — plain Leaflet, no react-leaflet wrapper                 */
/* ------------------------------------------------------------------ */

export interface RouteMapProps {
  points: GPSPoint[];
  height?: string;
  className?: string;
  /** Map tile style. Default: 'streets'. */
  tileStyle?: MapTileStyle;
  /** Index of point to highlight with a marker (for chart sync). */
  hoveredPointIndex?: number | null;
  /** Called when user hovers on route. pointIndex into GPSPoint[], or null. */
  onHoverPoint?: (pointIndex: number | null) => void;
  /** Display mode: plain route, pace heat map, or HR heat map. */
  mode?: HeatMapMode;
  /** Colored segments for pace/hr modes. */
  segments?: RouteSegment[];
  /** Km boundary markers for split visualization. */
  kmMarkers?: KmMarkerData[];
  /** Show/hide km markers layer. */
  showKmMarkers?: boolean;
  /** Lap boundary markers. */
  lapMarkers?: LapMarkerData[];
  /** Show/hide lap markers layer. */
  showLapMarkers?: boolean;
  /** Called when a km marker is clicked. */
  onKmMarkerClick?: (kmNumber: number) => void;
  /** Called when a lap marker is clicked. */
  onLapMarkerClick?: (lapNumber: number) => void;
  /** Highlighted km number (for table row hover sync). */
  highlightedKm?: number | null;
  /** Highlighted lap number (for table row hover sync). */
  highlightedLap?: number | null;
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
  tileStyle = 'streets',
  hoveredPointIndex,
  onHoverPoint,
  mode = 'route',
  segments,
  kmMarkers,
  showKmMarkers = false,
  lapMarkers,
  showLapMarkers = false,
  onKmMarkerClick,
  onLapMarkerClick,
  highlightedKm,
  highlightedLap,
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const hoverMarkerRef = useRef<L.CircleMarker | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const kmMarkerLayerRef = useRef<L.LayerGroup | null>(null);
  const lapMarkerLayerRef = useRef<L.LayerGroup | null>(null);
  const onHoverPointRef = useRef(onHoverPoint);
  onHoverPointRef.current = onHoverPoint;
  const onKmMarkerClickRef = useRef(onKmMarkerClick);
  onKmMarkerClickRef.current = onKmMarkerClick;
  const onLapMarkerClickRef = useRef(onLapMarkerClick);
  onLapMarkerClickRef.current = onLapMarkerClick;
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

    const tile = TILES[tileStyle] || TILES.streets;
    tileLayerRef.current = L.tileLayer(tile.url, {
      attribution: tile.attribution,
      maxZoom: tile.maxZoom,
    }).addTo(map);

    map.fitBounds(L.latLngBounds(positions), { padding: [30, 30] });

    return () => {
      hoverMarkerRef.current = null;
      routeLayerRef.current = null;
      tileLayerRef.current = null;
      kmMarkerLayerRef.current = null;
      lapMarkerLayerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, [positions.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // Tile layer swap (separate effect — no map reinit on style change)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      tileLayerRef.current.remove();
    }
    const tile = TILES[tileStyle] || TILES.streets;
    tileLayerRef.current = L.tileLayer(tile.url, {
      attribution: tile.attribution,
      maxZoom: tile.maxZoom,
    }).addTo(map);
  }, [tileStyle]);

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

  // Km marker layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (kmMarkerLayerRef.current) {
      kmMarkerLayerRef.current.remove();
      kmMarkerLayerRef.current = null;
    }

    if (!showKmMarkers || !kmMarkers || kmMarkers.length === 0) return;

    const layer = L.layerGroup().addTo(map);
    kmMarkerLayerRef.current = layer;

    for (const km of kmMarkers) {
      const isHighlighted = highlightedKm === km.km_number;
      const label = km.is_partial ? km.distance_km.toFixed(1) : String(km.km_number);

      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:24px;height:24px;border-radius:50%;
          background:${isHighlighted ? '#dbeafe' : '#fff'};
          border:2px solid ${isHighlighted ? '#3b82f6' : '#374151'};
          color:${isHighlighted ? '#1d4ed8' : '#374151'};
          font-size:10px;font-weight:600;
          display:flex;align-items:center;justify-content:center;
          box-shadow:0 1px 3px rgba(0,0,0,0.2);
        ">${label}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([km.lat, km.lng], { icon, interactive: true });
      marker.bindPopup(buildKmPopupHtml(km), { maxWidth: 200, className: 'km-split-popup' });
      marker.on('click', () => onKmMarkerClickRef.current?.(km.km_number));
      layer.addLayer(marker);
    }
  }, [kmMarkers, showKmMarkers, highlightedKm]);

  // Lap marker layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (lapMarkerLayerRef.current) {
      lapMarkerLayerRef.current.remove();
      lapMarkerLayerRef.current = null;
    }

    if (!showLapMarkers || !lapMarkers || lapMarkers.length === 0) return;

    const layer = L.layerGroup().addTo(map);
    lapMarkerLayerRef.current = layer;

    for (const lm of lapMarkers) {
      const isHighlighted = highlightedLap === lm.lap_number;
      const color = LAP_TYPE_COLORS[lm.type] || '#64748b';
      const dashArray = LAP_TYPE_DASHED.has(lm.type) ? '4 4' : undefined;

      const marker = L.circleMarker([lm.lat, lm.lng], {
        radius: isHighlighted ? 10 : 8,
        color,
        weight: isHighlighted ? 4 : 3,
        fillColor: '#ffffff',
        fillOpacity: 0.9,
        dashArray,
        interactive: true,
      });

      marker.bindPopup(buildLapPopupHtml(lm), { maxWidth: 200, className: 'lap-popup' });
      marker.on('click', () => onLapMarkerClickRef.current?.(lm.lap_number));
      layer.addLayer(marker);
    }
  }, [lapMarkers, showLapMarkers, highlightedLap]);

  if (positions.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className={`isolate rounded-[var(--radius-component-md)] overflow-hidden border border-[var(--color-border-default)] ${className}`}
      style={{ height }}
    />
  );
}
