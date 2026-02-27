/**
 * Builds colored route segments from GPS points for heat map visualization.
 */
import type { GPSPoint } from '@/api/training';
import { haversineMeters } from './gpsUtils';
import { paceColor, hrZoneColor } from './colorScale';
import type { HRZoneBoundary } from './colorScale';

export interface RouteSegment {
  /** LatLng tuples for the polyline segment. */
  positions: [number, number][];
  /** CSS color for this segment. */
  color: string;
  /** Display value (pace or HR). */
  value: number;
  /** Human-readable label for tooltip. */
  label: string;
}

/* ------------------------------------------------------------------ */
/*  Pace helpers                                                       */
/* ------------------------------------------------------------------ */

/** Calculate pace (min/km) from speed (m/s). Returns null if speed is 0. */
function speedToPace(speedMs: number): number | null {
  if (speedMs <= 0) return null;
  return 1000 / speedMs / 60; // min/km
}

/** Format pace as M:SS string. */
function formatPace(paceMinPerKm: number): string {
  const mins = Math.floor(paceMinPerKm);
  const secs = Math.round((paceMinPerKm - mins) * 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get pace for a point. Prefers `speed` field, falls back to
 * haversine-based calculation from neighboring points.
 */
function getPointPace(points: GPSPoint[], index: number): number | null {
  const p = points[index];

  // Use speed field if available
  if (p.speed != null && p.speed > 0) {
    return speedToPace(p.speed);
  }

  // Fallback: calculate from adjacent points
  if (index === 0) return null;
  const prev = points[index - 1];
  const dt = p.seconds - prev.seconds;
  if (dt <= 0) return null;

  const dist = haversineMeters(prev.lat, prev.lng, p.lat, p.lng);
  if (dist > 500) return null; // GPS glitch
  if (dist < 0.1) return null; // Stationary

  const speedMs = dist / dt;
  return speedToPace(speedMs);
}

/* ------------------------------------------------------------------ */
/*  Segment builder core                                               */
/* ------------------------------------------------------------------ */

interface SegmentAccumulator {
  positions: [number, number][];
  values: number[];
  cumulativeDistM: number;
}

function newAccumulator(lat: number, lng: number): SegmentAccumulator {
  return {
    positions: [[lat, lng]],
    values: [],
    cumulativeDistM: 0,
  };
}

/* ------------------------------------------------------------------ */
/*  Build pace segments                                                */
/* ------------------------------------------------------------------ */

export function buildPaceSegments(points: GPSPoint[], segmentLengthM = 100): RouteSegment[] {
  if (points.length < 2) return [];

  // Collect all valid paces for normalization
  const allPaces: number[] = [];
  for (let i = 0; i < points.length; i++) {
    const pace = getPointPace(points, i);
    if (pace != null && pace > 0 && pace < 30) allPaces.push(pace); // sanity: < 30 min/km
  }

  if (allPaces.length === 0) return [];

  // Relative scale: normalize to session min/max
  const minPace = Math.min(...allPaces);
  const maxPace = Math.max(...allPaces);
  const paceRange = maxPace - minPace || 1;

  const segments: RouteSegment[] = [];
  let acc = newAccumulator(points[0].lat, points[0].lng);

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const dist = haversineMeters(prev.lat, prev.lng, curr.lat, curr.lng);

    if (dist > 500) continue; // Skip GPS glitches

    acc.positions.push([curr.lat, curr.lng]);
    acc.cumulativeDistM += dist;

    const pace = getPointPace(points, i);
    if (pace != null && pace > 0 && pace < 30) {
      acc.values.push(pace);
    }

    // Flush segment when target length reached
    if (acc.cumulativeDistM >= segmentLengthM) {
      if (acc.values.length > 0 && acc.positions.length >= 2) {
        const avgPace = acc.values.reduce((a, b) => a + b, 0) / acc.values.length;
        // Higher t = faster (lower pace number = faster)
        const t = 1 - (avgPace - minPace) / paceRange;
        segments.push({
          positions: acc.positions,
          color: paceColor(t),
          value: avgPace,
          label: `${formatPace(avgPace)} /km`,
        });
      }
      // Start new segment from last point
      acc = newAccumulator(curr.lat, curr.lng);
    }
  }

  // Final segment
  if (acc.values.length > 0 && acc.positions.length >= 2) {
    const avgPace = acc.values.reduce((a, b) => a + b, 0) / acc.values.length;
    const t = 1 - (avgPace - minPace) / paceRange;
    segments.push({
      positions: acc.positions,
      color: paceColor(t),
      value: avgPace,
      label: `${formatPace(avgPace)} /km`,
    });
  }

  return segments;
}

/* ------------------------------------------------------------------ */
/*  Build HR segments                                                  */
/* ------------------------------------------------------------------ */

export function buildHRSegments(
  points: GPSPoint[],
  zones: HRZoneBoundary[],
  segmentLengthM = 100,
): RouteSegment[] {
  if (points.length < 2 || zones.length === 0) return [];

  const segments: RouteSegment[] = [];
  let acc = newAccumulator(points[0].lat, points[0].lng);

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const dist = haversineMeters(prev.lat, prev.lng, curr.lat, curr.lng);

    if (dist > 500) continue;

    acc.positions.push([curr.lat, curr.lng]);
    acc.cumulativeDistM += dist;

    if (curr.hr != null) {
      acc.values.push(curr.hr);
    }

    if (acc.cumulativeDistM >= segmentLengthM) {
      if (acc.values.length > 0 && acc.positions.length >= 2) {
        const avgHr = Math.round(acc.values.reduce((a, b) => a + b, 0) / acc.values.length);
        segments.push({
          positions: acc.positions,
          color: hrZoneColor(avgHr, zones),
          value: avgHr,
          label: `${avgHr} bpm`,
        });
      }
      acc = newAccumulator(curr.lat, curr.lng);
    }
  }

  // Final segment
  if (acc.values.length > 0 && acc.positions.length >= 2) {
    const avgHr = Math.round(acc.values.reduce((a, b) => a + b, 0) / acc.values.length);
    segments.push({
      positions: acc.positions,
      color: hrZoneColor(avgHr, zones),
      value: avgHr,
      label: `${avgHr} bpm`,
    });
  }

  return segments;
}
