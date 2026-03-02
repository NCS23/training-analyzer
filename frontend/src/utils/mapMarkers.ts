/**
 * Map marker types, colors, and popup builders for km-split
 * and lap markers on the route map.
 */

/* ------------------------------------------------------------------ */
/*  Km Marker                                                          */
/* ------------------------------------------------------------------ */

export interface KmMarkerData {
  km_number: number;
  lat: number;
  lng: number;
  pace_formatted: string | null;
  pace_corrected_formatted: string | null;
  avg_hr_bpm: number | null;
  duration_formatted: string;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  is_partial: boolean;
  distance_km: number;
}

export function buildKmPopupHtml(km: KmMarkerData): string {
  const title = km.is_partial ? `${km.distance_km} km` : `Km ${km.km_number}`;
  const lines = [`<b>${title}</b>`];

  if (km.pace_formatted) lines.push(`Pace: ${km.pace_formatted} /km`);
  if (km.pace_corrected_formatted) lines.push(`GAP: ${km.pace_corrected_formatted} /km`);
  if (km.avg_hr_bpm != null) lines.push(`HF: ${km.avg_hr_bpm} bpm`);
  lines.push(`Dauer: ${km.duration_formatted}`);

  if (km.elevation_gain_m != null || km.elevation_loss_m != null) {
    const parts: string[] = [];
    if (km.elevation_gain_m != null) parts.push(`↑${km.elevation_gain_m}m`);
    if (km.elevation_loss_m != null) parts.push(`↓${km.elevation_loss_m}m`);
    lines.push(parts.join('  '));
  }

  return lines.join('<br>');
}

/* ------------------------------------------------------------------ */
/*  Lap Marker                                                         */
/* ------------------------------------------------------------------ */

export interface LapMarkerData {
  lap_number: number;
  lat: number;
  lng: number;
  /** Effective type (user_override || suggested_type || 'unclassified'). */
  type: string;
  pace_formatted: string | null;
  duration_formatted: string;
  avg_hr_bpm: number | null;
  distance_km: number | null;
}

/** Color per lap type — uses primary/secondary palette for non-semantic differentiation. */
export const LAP_TYPE_COLORS: Record<string, string> = {
  interval: '#4f46e5',   // primary-2-600 (indigo)
  tempo: '#6366f1',      // primary-2-500 (indigo)
  warmup: '#94a3b8',     // secondary-1-400 (slate)
  cooldown: '#94a3b8',   // secondary-1-400 (slate)
  pause: '#6b7280',      // secondary-1-500 (slate)
  recovery: '#7dd3fc',   // primary-1-300 (sky)
  longrun: '#0284c7',    // primary-1-600 (sky)
  working: '#0ea5e9',    // primary-1-500 (sky)
  unclassified: '#64748b', // secondary-1-500 (slate)
};

/** Lap types rendered with dashed stroke. */
export const LAP_TYPE_DASHED = new Set(['warmup', 'cooldown']);

/** German display labels for lap types. */
export const LAP_TYPE_LABELS: Record<string, string> = {
  interval: 'Intervall',
  tempo: 'Tempo',
  warmup: 'Warmup',
  cooldown: 'Cooldown',
  pause: 'Pause',
  recovery: 'Erholung',
  longrun: 'Langer Lauf',
  working: 'Arbeit',
  unclassified: 'Unklassifiziert',
};

export function buildLapPopupHtml(lap: LapMarkerData): string {
  const typeLabel = LAP_TYPE_LABELS[lap.type] || lap.type;
  const lines = [`<b>Lap ${lap.lap_number}</b> — ${typeLabel}`];

  if (lap.pace_formatted) lines.push(`Pace: ${lap.pace_formatted} /km`);
  if (lap.avg_hr_bpm != null) lines.push(`HF: ${lap.avg_hr_bpm} bpm`);
  lines.push(`Dauer: ${lap.duration_formatted}`);
  if (lap.distance_km != null) lines.push(`Distanz: ${lap.distance_km} km`);

  return lines.join('<br>');
}
