/**
 * Color scale utilities for Pace/HR heat map visualization.
 */

export type HeatMapMode = 'route' | 'pace' | 'hr';

export interface HRZoneBoundary {
  zone: number;
  lowerBpm: number;
  upperBpm: number;
  color: string;
  name: string;
}

/* ------------------------------------------------------------------ */
/*  Karvonen HR Zone calculation (mirrors backend hr_zone_calculator)  */
/* ------------------------------------------------------------------ */

const KARVONEN_ZONE_DEFS = [
  { zone: 1, name: 'Recovery', pctMin: 0.5, pctMax: 0.6, color: '#94a3b8' },
  { zone: 2, name: 'Base', pctMin: 0.6, pctMax: 0.7, color: '#10b981' },
  { zone: 3, name: 'Tempo', pctMin: 0.7, pctMax: 0.8, color: '#f59e0b' },
  { zone: 4, name: 'Threshold', pctMin: 0.8, pctMax: 0.9, color: '#f97316' },
  { zone: 5, name: 'VO2max', pctMin: 0.9, pctMax: 1.0, color: '#ef4444' },
] as const;

function karvonenBpm(restingHr: number, maxHr: number, intensity: number): number {
  return Math.round(restingHr + (maxHr - restingHr) * intensity);
}

/** Compute Karvonen 5-zone HR boundaries. */
export function computeHRZoneBoundaries(restingHr: number, maxHr: number): HRZoneBoundary[] {
  return KARVONEN_ZONE_DEFS.map((z) => ({
    zone: z.zone,
    lowerBpm: karvonenBpm(restingHr, maxHr, z.pctMin),
    upperBpm: karvonenBpm(restingHr, maxHr, z.pctMax),
    color: z.color,
    name: z.name,
  }));
}

/* ------------------------------------------------------------------ */
/*  Pace color scale                                                   */
/* ------------------------------------------------------------------ */

/**
 * Interpolate between green (fast) → yellow → red (slow).
 * @param t Normalized value 0..1 where 0=fastest, 1=slowest
 */
export function paceColor(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  let r: number, g: number, b: number;

  if (clamped < 0.5) {
    // Green → Yellow
    const s = clamped * 2;
    r = Math.round(s * 255);
    g = 220;
    b = 30;
  } else {
    // Yellow → Red
    const s = (clamped - 0.5) * 2;
    r = 255;
    g = Math.round(220 * (1 - s));
    b = 30;
  }

  return `rgb(${r},${g},${b})`;
}

/* ------------------------------------------------------------------ */
/*  HR zone color lookup                                               */
/* ------------------------------------------------------------------ */

/** Get the zone color for a given HR value. */
export function hrZoneColor(hr: number, zones: HRZoneBoundary[]): string {
  // Below zone 1
  if (hr < zones[0].lowerBpm) return zones[0].color;

  for (let i = 0; i < zones.length; i++) {
    const z = zones[i];
    if (i === zones.length - 1) {
      // Last zone: everything above lower
      if (hr >= z.lowerBpm) return z.color;
    } else if (hr >= z.lowerBpm && hr < z.upperBpm) {
      return z.color;
    }
  }

  // Fallback: last zone
  return zones[zones.length - 1].color;
}
