/**
 * Interactive Leaflet map for creating and editing training routes.
 *
 * Part of Epic #508 (Routenplaner), Story #527.
 */

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { TILES } from './tileStyles';
import type { Waypoint } from '@/api/routes';

export interface RouteEditorMapProps {
  waypoints: Waypoint[];
  routePoints: Waypoint[];
  onWaypointAdd: (lat: number, lng: number) => void;
  onWaypointMove: (index: number, lat: number, lng: number) => void;
  onWaypointDelete: (index: number) => void;
  routing?: boolean;
  height?: string;
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

export function RouteEditorMap({
  waypoints,
  routePoints,
  onWaypointAdd,
  onWaypointMove,
  onWaypointDelete,
  routing = false,
  height = '60vh',
}: RouteEditorMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);
  const polylineRef = useRef<L.Polyline | null>(null);
  const callbacksRef = useRef({ onWaypointAdd, onWaypointMove, onWaypointDelete });

  useEffect(() => {
    callbacksRef.current = { onWaypointAdd, onWaypointMove, onWaypointDelete };
  }, [onWaypointAdd, onWaypointMove, onWaypointDelete]);

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const tile = TILES.outdoor;
    const map = L.map(containerRef.current, {
      scrollWheelZoom: true,
      maxZoom: tile.maxZoom ?? 19,
      zoomControl: true,
    }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer(tile.url, { attribution: tile.attribution, maxZoom: tile.maxZoom ?? 19 }).addTo(
      map,
    );

    map.on('click', (e: L.LeafletMouseEvent) => {
      callbacksRef.current.onWaypointAdd(e.latlng.lat, e.latlng.lng);
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
    polylineRef.current?.remove();
    polylineRef.current = null;

    const points = routePoints.length > 0 ? routePoints : waypoints;
    if (points.length < 2) return;

    polylineRef.current = L.polyline(
      points.map((p) => [p.lat, p.lng] as L.LatLngTuple),
      {
        color: '#3b82f6',
        weight: 4,
        opacity: routing ? 0.4 : 0.8,
        dashArray: routing ? '8 8' : undefined,
      },
    ).addTo(map);
  }, [routePoints, waypoints, routing]);

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
      <div
        ref={containerRef}
        style={{ height, minHeight: '250px' }}
        className="w-full rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] z-0"
      />
      <MapOverlays routing={routing} empty={waypoints.length === 0} />
    </div>
  );
}
