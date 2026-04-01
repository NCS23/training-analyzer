/**
 * Interactive Leaflet map for creating and editing training routes.
 *
 * Part of Epic #508 (Routenplaner), Story #527.
 */

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { TILES } from './tileStyles';
import type { Waypoint, RouteSegment } from '@/api/routes';
import { SEGMENT_TYPE_COLORS } from '@/constants/segmentColors';

export interface RouteEditorMapProps {
  waypoints: Waypoint[];
  routePoints: Waypoint[];
  onWaypointAdd: (lat: number, lng: number) => void;
  onWaypointMove: (index: number, lat: number, lng: number) => void;
  onWaypointDelete: (index: number) => void;
  routing?: boolean;
  height?: string;
  segments?: RouteSegment[];
  readOnly?: boolean;
}

const DEFAULT_CENTER: L.LatLngTuple = [53.55, 9.99]; // Hamburg
const DEFAULT_ZOOM = 13;

const WAYPOINT_STYLE: L.CircleMarkerOptions = {
  radius: 10,
  color: '#3b82f6',
  fillColor: '#ffffff',
  fillOpacity: 1,
  weight: 3,
};

function getMarkerStyle(index: number, total: number): L.CircleMarkerOptions {
  if (index === 0)
    return { ...WAYPOINT_STYLE, color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.8 };
  if (index === total - 1 && total > 1)
    return { ...WAYPOINT_STYLE, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.8 };
  return WAYPOINT_STYLE;
}

function getMarkerLabel(index: number, total: number): string {
  if (index === 0) return 'S';
  if (index === total - 1 && total > 1) return 'Z';
  return String(index + 1);
}

/** Create draggable waypoint markers on the map. */
function createWaypointMarkers(
  map: L.Map,
  waypoints: Waypoint[],
  callbacks: {
    onWaypointMove: (i: number, lat: number, lng: number) => void;
    onWaypointDelete: (i: number) => void;
  },
): L.CircleMarker[] {
  return waypoints.map((wp, index) => {
    const marker = L.circleMarker([wp.lat, wp.lng], getMarkerStyle(index, waypoints.length)).addTo(
      map,
    );

    marker.bindTooltip(getMarkerLabel(index, waypoints.length), {
      permanent: true,
      direction: 'center',
      className: 'route-wp-label',
    });

    marker.on('click', (e: L.LeafletMouseEvent) => {
      L.DomEvent.stopPropagation(e);
      callbacks.onWaypointDelete(index);
    });

    // Drag via mousedown + mousemove
    let dragging = false;
    marker.on('mousedown', (e: L.LeafletMouseEvent) => {
      L.DomEvent.stopPropagation(e);
      dragging = true;
      map.dragging.disable();

      const onMove = (me: L.LeafletMouseEvent) => {
        if (dragging) marker.setLatLng(me.latlng);
      };
      const onUp = (ue: L.LeafletMouseEvent) => {
        if (!dragging) return;
        dragging = false;
        map.dragging.enable();
        map.off('mousemove', onMove);
        map.off('mouseup', onUp);
        callbacks.onWaypointMove(index, ue.latlng.lat, ue.latlng.lng);
      };

      map.on('mousemove', onMove);
      map.on('mouseup', onUp);
    });

    return marker;
  });
}

function MapOverlays({ routing, empty }: { routing: boolean; empty: boolean }) {
  return (
    <>
      {routing && (
        <div className="absolute top-3 right-3 z-[1000] rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] shadow-[var(--shadow-sm)]">
          Route wird berechnet…
        </div>
      )}
      {empty && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[1000]">
          <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)]/90 px-4 py-3 text-sm text-[var(--color-text-muted)] shadow-[var(--shadow-sm)]">
            Klicke auf die Karte um Wegpunkte zu setzen
          </div>
        </div>
      )}
    </>
  );
}

/** Erstelle farbige Polylines basierend auf Segmenten. */
function createSegmentPolylines(
  map: L.Map,
  routePoints: Waypoint[],
  segments: RouteSegment[],
): L.Polyline[] {
  if (routePoints.length < 2 || segments.length === 0) return [];

  // Berechne kumulative Distanz für jeden Punkt
  const cumDist: number[] = [0];
  for (let i = 1; i < routePoints.length; i++) {
    const dlat = routePoints[i].lat - routePoints[i - 1].lat;
    const dlng = routePoints[i].lng - routePoints[i - 1].lng;
    cumDist.push(cumDist[i - 1] + Math.sqrt(dlat * dlat + dlng * dlng) * 111.32);
  }
  const totalKm = cumDist[cumDist.length - 1];
  if (totalKm <= 0) return [];

  return segments.map((seg) => {
    const startFrac = seg.start_km / totalKm;
    const endFrac = seg.end_km / totalKm;
    const startIdx = Math.max(
      0,
      cumDist.findIndex((d) => d / totalKm >= startFrac),
    );
    const endIdx = Math.min(
      routePoints.length - 1,
      cumDist.findIndex((d) => d / totalKm >= endFrac),
    );
    const segPoints = routePoints.slice(startIdx, endIdx + 1);
    const color = SEGMENT_TYPE_COLORS[seg.segment_type] ?? '#3b82f6';

    return L.polyline(
      segPoints.map((p) => [p.lat, p.lng] as L.LatLngTuple),
      { color, weight: 5, opacity: 0.85 },
    ).addTo(map);
  });
}

// eslint-disable-next-line max-lines-per-function -- Karten-Orchestrator mit mehreren unabhängigen useEffect-Blöcken
export function RouteEditorMap({
  waypoints,
  routePoints,
  onWaypointAdd,
  onWaypointMove,
  onWaypointDelete,
  routing = false,
  height = '60vh',
  segments = [],
  readOnly = false,
}: RouteEditorMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);
  const polylineRef = useRef<L.Polyline | null>(null);
  const polylineCasingRef = useRef<L.Polyline | null>(null);
  const segmentLinesRef = useRef<L.Polyline[]>([]);
  const callbacksRef = useRef({ onWaypointAdd, onWaypointMove, onWaypointDelete });
  // readOnly als Ref damit der Klick-Handler reaktiv ist ohne Map-Neustart
  const readOnlyRef = useRef(readOnly);

  useEffect(() => {
    callbacksRef.current = { onWaypointAdd, onWaypointMove, onWaypointDelete };
  }, [onWaypointAdd, onWaypointMove, onWaypointDelete]);

  useEffect(() => {
    readOnlyRef.current = readOnly;
    // Cursor-Stil für Edit-Modus anzeigen
    if (mapRef.current) {
      const container = mapRef.current.getContainer();
      container.style.cursor = readOnly ? '' : 'crosshair';
    }
  }, [readOnly]);

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Standard OSM: gute Lesbarkeit, Sky-500 Route kontrastiert gut
    const tile = TILES.streets;
    const map = L.map(containerRef.current, {
      scrollWheelZoom: true,
      maxZoom: tile.maxZoom ?? 19,
      zoomControl: true,
    }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer(tile.url, { attribution: tile.attribution, maxZoom: tile.maxZoom ?? 19 }).addTo(
      map,
    );

    // Klick-Handler prüft readOnlyRef — reagiert auf Modus-Wechsel ohne Map-Neustart
    map.on('click', (e: L.LeafletMouseEvent) => {
      if (!readOnlyRef.current) {
        callbacksRef.current.onWaypointAdd(e.latlng.lat, e.latlng.lng);
      }
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update route polyline
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    polylineCasingRef.current?.remove();
    polylineCasingRef.current = null;
    polylineRef.current?.remove();
    polylineRef.current = null;

    const points = routePoints.length > 0 ? routePoints : waypoints;
    if (points.length < 2) return;

    const cs = getComputedStyle(document.documentElement);
    // Leaflet benötigt rohe CSS-Werte — semantische Tokens zur Laufzeit auflösen
    const routeColor = cs.getPropertyValue('--color-bg-primary').trim() || '#0ea5e9';
    const casingColor = cs.getPropertyValue('--color-bg-surface').trim() || '#ffffff';

    const latlngs = points.map((p) => [p.lat, p.lng] as L.LatLngTuple);
    const opacity = routing ? 0.45 : 1;

    // Weißes Casing unter der Route für Sichtbarkeit auf jedem Kartenstil
    polylineCasingRef.current = L.polyline(latlngs, {
      color: casingColor,
      weight: 9,
      opacity,
      dashArray: routing ? '8 8' : undefined,
    }).addTo(map);

    polylineRef.current = L.polyline(latlngs, {
      color: routeColor,
      weight: 5,
      opacity,
      dashArray: routing ? '8 8' : undefined,
    }).addTo(map);
  }, [routePoints, waypoints, routing]);

  // Update segment color overlays
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    segmentLinesRef.current.forEach((l) => l.remove());
    segmentLinesRef.current = [];

    if (segments.length > 0 && routePoints.length > 1) {
      segmentLinesRef.current = createSegmentPolylines(map, routePoints, segments);
    }
  }, [segments, routePoints]);

  // Update waypoint markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = createWaypointMarkers(map, waypoints, callbacksRef.current);

    if (waypoints.length > 0) {
      const bounds = L.latLngBounds(waypoints.map((wp) => [wp.lat, wp.lng] as L.LatLngTuple));
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
    }
  }, [waypoints]);

  return (
    <div className="relative">
      <div ref={containerRef} style={{ height, minHeight: '250px' }} className="w-full z-0" />
      <MapOverlays routing={routing} empty={!readOnly && waypoints.length === 0} />
    </div>
  );
}
