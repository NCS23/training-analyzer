/**
 * GPS utility functions for distance calculation, elevation profiles,
 * and altitude smoothing.
 */
import type { GPSPoint } from '@/api/training';

export interface ElevationDataPoint {
  /** Cumulative distance from start in km. */
  distanceKm: number;
  /** Altitude in meters. */
  altitudeM: number;
  /** Index into the original GPSPoint[] array (for map sync). */
  pointIndex: number;
  /** Elapsed seconds from start. */
  seconds: number;
  /** Heart rate if available. */
  hr?: number;
  /** Pace in min/km if available. */
  paceMinKm?: number;
}

export interface ElevationSummary {
  minAltitudeM: number;
  maxAltitudeM: number;
  totalAscentM: number;
  totalDescentM: number;
}

/** Haversine distance in meters between two lat/lng pairs. */
export function haversineMeters(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371000;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const dphi = ((lat2 - lat1) * Math.PI) / 180;
  const dlambda = ((lng2 - lng1) * Math.PI) / 180;
  const a = Math.sin(dphi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Build elevation profile data from GPS points.
 * Filters out points without altitude data. Computes cumulative
 * distance via haversine.
 */
export function buildElevationProfile(points: GPSPoint[]): ElevationDataPoint[] {
  if (points.length === 0) return [];

  const result: ElevationDataPoint[] = [];
  let cumulativeDistM = 0;

  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (p.alt == null) continue;

    if (i > 0) {
      const prev = points[i - 1];
      const dist = haversineMeters(prev.lat, prev.lng, p.lat, p.lng);
      // Skip GPS glitches: > 500m between consecutive seconds
      if (dist < 500) {
        cumulativeDistM += dist;
      }
    }

    // Calculate pace from speed or haversine fallback
    let paceMinKm: number | undefined;
    if (p.speed != null && p.speed > 0) {
      paceMinKm = 1000 / p.speed / 60;
    } else if (i > 0) {
      const prev = points[i - 1];
      const dt = p.seconds - prev.seconds;
      const dist = haversineMeters(prev.lat, prev.lng, p.lat, p.lng);
      if (dt > 0 && dist > 0.1 && dist < 500) {
        paceMinKm = 1000 / (dist / dt) / 60;
      }
    }
    // Clamp unreasonable paces
    if (paceMinKm != null && (paceMinKm < 1 || paceMinKm > 30)) {
      paceMinKm = undefined;
    }

    result.push({
      distanceKm: Math.round((cumulativeDistM / 1000) * 1000) / 1000,
      altitudeM: p.alt,
      pointIndex: i,
      seconds: p.seconds,
      hr: p.hr,
      paceMinKm,
    });
  }

  return result;
}

/**
 * Smooth altitude data using a simple moving average.
 * Only smooths the altitudeM values; other fields are preserved.
 */
export function smoothAltitude(data: ElevationDataPoint[], windowSize = 5): ElevationDataPoint[] {
  if (data.length <= windowSize) return data;

  const half = Math.floor(windowSize / 2);
  return data.map((point, i) => {
    const start = Math.max(0, i - half);
    const end = Math.min(data.length - 1, i + half);
    let sum = 0;
    let count = 0;
    for (let j = start; j <= end; j++) {
      sum += data[j].altitudeM;
      count++;
    }
    return { ...point, altitudeM: Math.round((sum / count) * 10) / 10 };
  });
}

/** Calculate min/max altitude from elevation profile data. */
export function getElevationSummary(data: ElevationDataPoint[]): ElevationSummary | null {
  if (data.length === 0) return null;

  let min = Infinity;
  let max = -Infinity;

  for (const d of data) {
    if (d.altitudeM < min) min = d.altitudeM;
    if (d.altitudeM > max) max = d.altitudeM;
  }

  return {
    minAltitudeM: Math.round(min),
    maxAltitudeM: Math.round(max),
    totalAscentM: 0, // Will be filled from backend data
    totalDescentM: 0,
  };
}
