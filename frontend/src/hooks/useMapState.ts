import { useState, useMemo, useEffect } from 'react';
import type { MapTileStyle } from '@/features/maps';
import type { HeatMapMode } from '@/utils/colorScale';
import { computeHRZoneBoundaries } from '@/utils/colorScale';
import { buildPaceSegments, buildHRSegments } from '@/utils/segmentBuilder';
import type { KmMarkerData, LapMarkerData } from '@/utils/mapMarkers';
import type { GPSTrack, KmSplit, LapDetail } from '@/api/training';

export interface MapState {
  // Map display
  tileStyle: MapTileStyle;
  setTileStyle: (style: MapTileStyle) => void;
  mapMode: HeatMapMode;
  setMapMode: (mode: HeatMapMode) => void;
  hoveredPointIndex: number | null;
  setHoveredPointIndex: (index: number | null) => void;

  // Marker toggles
  showKmMarkers: boolean;
  setShowKmMarkers: (show: boolean) => void;
  showLapMarkers: boolean;
  setShowLapMarkers: (show: boolean) => void;
  highlightedKm: number | null;
  setHighlightedKm: (km: number | null) => void;
  highlightedLap: number | null;
  setHighlightedLap: (lap: number | null) => void;

  // Splits tab
  splitsTab: 'laps' | 'km';
  setSplitsTab: (tab: 'laps' | 'km') => void;

  // Computed
  hrZoneBoundaries: ReturnType<typeof computeHRZoneBoundaries> | null;
  mapSegments: ReturnType<typeof buildPaceSegments> | undefined;
  paceRange: { min: number; max: number } | null;
  kmMarkerData: KmMarkerData[] | undefined;
  lapMarkerData: LapMarkerData[] | undefined;
  canShowHR: boolean;
}

interface UseMapStateParams {
  athleteRestingHr: number | null | undefined;
  athleteMaxHr: number | null | undefined;
  gpsTrack: GPSTrack | null;
  kmSplits: KmSplit[] | null;
  localLaps: LapDetail[];
}

// eslint-disable-next-line max-lines-per-function -- hook with many state + computed values
export function useMapState({
  athleteRestingHr,
  athleteMaxHr,
  gpsTrack,
  kmSplits,
  localLaps,
}: UseMapStateParams): MapState {
  // Map display state
  const [tileStyle, setTileStyle] = useState<MapTileStyle>(() => {
    try {
      const stored = localStorage.getItem('mapTileStyle');
      return (stored as MapTileStyle) || 'streets';
    } catch {
      return 'streets';
    }
  });
  const [mapMode, setMapMode] = useState<HeatMapMode>('route');
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(null);

  // Marker toggles
  const [showKmMarkers, setShowKmMarkers] = useState(true);
  const [showLapMarkers, setShowLapMarkers] = useState(true);
  const [highlightedKm, setHighlightedKm] = useState<number | null>(null);
  const [highlightedLap, setHighlightedLap] = useState<number | null>(null);

  // Splits tab
  const [splitsTab, setSplitsTab] = useState<'laps' | 'km'>('laps');

  // Persist tile style
  useEffect(() => {
    try {
      localStorage.setItem('mapTileStyle', tileStyle);
    } catch {
      // localStorage unavailable
    }
  }, [tileStyle]);

  // Computed values
  const hrZoneBoundaries = useMemo(() => {
    if (athleteRestingHr != null && athleteMaxHr != null) {
      return computeHRZoneBoundaries(athleteRestingHr, athleteMaxHr);
    }
    return null;
  }, [athleteRestingHr, athleteMaxHr]);

  const mapSegments = useMemo(() => {
    if (!gpsTrack || gpsTrack.points.length < 2) return undefined;
    if (mapMode === 'pace') return buildPaceSegments(gpsTrack.points);
    if (mapMode === 'hr' && hrZoneBoundaries)
      return buildHRSegments(gpsTrack.points, hrZoneBoundaries);
    return undefined;
  }, [gpsTrack, mapMode, hrZoneBoundaries]);

  const paceRange = useMemo(() => {
    if (mapMode !== 'pace' || !mapSegments || mapSegments.length === 0) return null;
    const paces = mapSegments.map((s) => s.value);
    return { min: Math.min(...paces), max: Math.max(...paces) };
  }, [mapMode, mapSegments]);

  const kmMarkerData = useMemo((): KmMarkerData[] | undefined => {
    if (!kmSplits) return undefined;
    return kmSplits
      .filter((s) => s.boundary_lat != null && s.boundary_lng != null)
      .map((s) => ({
        km_number: s.km_number,
        lat: s.boundary_lat!,
        lng: s.boundary_lng!,
        pace_formatted: s.pace_formatted,
        pace_corrected_formatted: s.pace_corrected_formatted,
        avg_hr_bpm: s.avg_hr_bpm,
        duration_formatted: s.duration_formatted,
        elevation_gain_m: s.elevation_gain_m,
        elevation_loss_m: s.elevation_loss_m,
        is_partial: s.is_partial,
        distance_km: s.distance_km,
      }));
  }, [kmSplits]);

  const lapMarkerData = useMemo((): LapMarkerData[] | undefined => {
    if (!localLaps || localLaps.length === 0 || !gpsTrack) return undefined;
    const pts = gpsTrack.points;
    if (pts.length === 0) return undefined;

    return localLaps
      .filter((lap) => lap.start_seconds != null)
      .map((lap) => {
        const targetSec = lap.start_seconds!;
        let lo = 0;
        let hi = pts.length - 1;
        while (lo < hi) {
          const mid = (lo + hi) >> 1;
          if (pts[mid].seconds < targetSec) lo = mid + 1;
          else hi = mid;
        }
        const pt = pts[lo];
        const type = lap.user_override || lap.suggested_type || 'unclassified';
        return {
          lap_number: lap.lap_number,
          lat: pt.lat,
          lng: pt.lng,
          type,
          pace_formatted: lap.pace_formatted,
          duration_formatted: lap.duration_formatted,
          avg_hr_bpm: lap.avg_hr_bpm,
          distance_km: lap.distance_km,
        };
      });
  }, [localLaps, gpsTrack]);

  return {
    tileStyle,
    setTileStyle,
    mapMode,
    setMapMode,
    hoveredPointIndex,
    setHoveredPointIndex,
    showKmMarkers,
    setShowKmMarkers,
    showLapMarkers,
    setShowLapMarkers,
    highlightedKm,
    setHighlightedKm,
    highlightedLap,
    setHighlightedLap,
    splitsTab,
    setSplitsTab,
    hrZoneBoundaries,
    mapSegments,
    paceRange,
    kmMarkerData,
    lapMarkerData,
    canShowHR: hrZoneBoundaries != null,
  };
}
