import { useState, useCallback, useEffect, useRef } from 'react';
import { snapRoute, getRoute, createRoute, updateRoute } from '@/api/routes';
import type { Waypoint, TrainingRouteResponse } from '@/api/routes';

export interface UseRouteEditorReturn {
  waypoints: Waypoint[];
  routePoints: Waypoint[];
  name: string;
  distanceKm: number;
  elevationGainM: number;
  elevationLossM: number;
  loading: boolean;
  routing: boolean;
  saving: boolean;
  dirty: boolean;
  addWaypoint: (lat: number, lng: number) => void;
  moveWaypoint: (index: number, lat: number, lng: number) => void;
  deleteWaypoint: (index: number) => void;
  setName: (name: string) => void;
  save: () => Promise<number | null>;
  loadRoute: (routeId: number) => Promise<void>;
}

/** Berechne Elevation Gain/Loss aus Höhendaten. */
function computeElevation(points: Waypoint[]): { gain: number; loss: number } {
  const alts = points.filter((p) => p.alt != null).map((p) => p.alt!);
  let gain = 0;
  let loss = 0;
  for (let i = 1; i < alts.length; i++) {
    const diff = alts[i] - alts[i - 1];
    if (diff > 1) gain += diff;
    else if (diff < -1) loss += Math.abs(diff);
  }
  return { gain: Math.round(gain), loss: Math.round(loss) };
}

/** Extrahiere gleichmäßig verteilte Marker-Waypoints aus einer vollen Route. */
function extractMarkerWaypoints(allPoints: Waypoint[], maxMarkers = 20): Waypoint[] {
  if (allPoints.length <= maxMarkers) return [...allPoints];
  const step = Math.max(1, Math.floor(allPoints.length / maxMarkers));
  return allPoints.filter((_, i) => i === 0 || i === allPoints.length - 1 || i % step === 0);
}

interface EditorState {
  waypoints: Waypoint[];
  routePoints: Waypoint[];
  name: string;
  distanceKm: number;
  elevationGainM: number;
  elevationLossM: number;
  loading: boolean;
  routing: boolean;
  saving: boolean;
  dirty: boolean;
  existingRouteId: number | null;
  existingRoute: TrainingRouteResponse | null;
}

function useRouteSnapping(setState: React.Dispatch<React.SetStateAction<EditorState>>) {
  const abortRef = useRef<AbortController | null>(null);

  const recalculate = useCallback(
    async (wps: Waypoint[]) => {
      if (wps.length < 2) {
        setState((s) => ({
          ...s,
          routePoints: wps,
          distanceKm: 0,
          elevationGainM: 0,
          elevationLossM: 0,
        }));
        return;
      }
      abortRef.current?.abort();
      abortRef.current = new AbortController();
      setState((s) => ({ ...s, routing: true }));
      try {
        const result = await snapRoute(wps);
        const elev = computeElevation(result.points);
        setState((s) => ({
          ...s,
          routePoints: result.points,
          distanceKm: result.distance_km,
          elevationGainM: elev.gain,
          elevationLossM: elev.loss,
          routing: false,
        }));
      } catch {
        setState((s) => ({ ...s, routePoints: wps, routing: false }));
      }
    },
    [setState],
  );

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

  return recalculate;
}

export function useRouteEditor(): UseRouteEditorReturn {
  const [state, setState] = useState<EditorState>({
    waypoints: [],
    routePoints: [],
    name: '',
    distanceKm: 0,
    elevationGainM: 0,
    elevationLossM: 0,
    loading: false,
    routing: false,
    saving: false,
    dirty: false,
    existingRouteId: null,
    existingRoute: null,
  });

  const recalculate = useRouteSnapping(setState);

  const addWaypoint = useCallback(
    (lat: number, lng: number) => {
      setState((s) => {
        const wp: Waypoint = { lat: Number(lat.toFixed(6)), lng: Number(lng.toFixed(6)) };
        const newWps = [...s.waypoints, wp];
        recalculate(newWps);
        return { ...s, waypoints: newWps, dirty: true };
      });
    },
    [recalculate],
  );

  const moveWaypoint = useCallback(
    (index: number, lat: number, lng: number) => {
      setState((s) => {
        const newWps = [...s.waypoints];
        newWps[index] = {
          ...newWps[index],
          lat: Number(lat.toFixed(6)),
          lng: Number(lng.toFixed(6)),
        };
        recalculate(newWps);
        return { ...s, waypoints: newWps, dirty: true };
      });
    },
    [recalculate],
  );

  const deleteWaypoint = useCallback(
    (index: number) => {
      setState((s) => {
        const newWps = s.waypoints.filter((_, i) => i !== index);
        recalculate(newWps);
        return { ...s, waypoints: newWps, dirty: true };
      });
    },
    [recalculate],
  );

  const setName = useCallback((n: string) => {
    setState((s) => ({ ...s, name: n, dirty: true }));
  }, []);

  const save = useCallback(async (): Promise<number | null> => {
    if (state.waypoints.length < 2 || !state.name.trim()) return null;
    setState((s) => ({ ...s, saving: true }));
    try {
      const data = {
        name: state.name.trim(),
        distance_km: state.distanceKm,
        elevation_gain_m: state.elevationGainM,
        elevation_loss_m: state.elevationLossM,
        waypoints: state.routePoints.length > 0 ? state.routePoints : state.waypoints,
        route_segments: state.existingRoute?.route_segments ?? undefined,
        pacing_strategy: state.existingRoute?.pacing_strategy ?? undefined,
        tags: state.existingRoute?.tags ?? undefined,
      };
      const result = state.existingRouteId
        ? await updateRoute(state.existingRouteId, data)
        : await createRoute(data);
      setState((s) => ({ ...s, saving: false, dirty: false, existingRouteId: result.id }));
      return result.id;
    } catch (e) {
      setState((s) => ({ ...s, saving: false }));
      throw e;
    }
  }, [state]);

  const loadRoute = useCallback(async (routeId: number) => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const route = await getRoute(routeId);
      setState((s) => ({
        ...s,
        loading: false,
        existingRouteId: route.id,
        existingRoute: route,
        name: route.name,
        distanceKm: route.distance_km,
        elevationGainM: route.elevation_gain_m,
        elevationLossM: route.elevation_loss_m,
        routePoints: route.waypoints,
        waypoints: extractMarkerWaypoints(route.waypoints),
        dirty: false,
      }));
    } catch (e) {
      setState((s) => ({ ...s, loading: false }));
      throw e;
    }
  }, []);

  return { ...state, addWaypoint, moveWaypoint, deleteWaypoint, setName, save, loadRoute };
}
