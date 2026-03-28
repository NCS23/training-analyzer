/**
 * Segment type colors and labels for route planning.
 * Uses canonical segment types from taxonomy.
 */

/** Farben für Segment-Typen auf der Karte und in der Segment-Leiste. */
export const SEGMENT_TYPE_COLORS: Record<string, string> = {
  warmup: '#22c55e', // grün
  cooldown: '#22c55e', // grün
  steady: '#3b82f6', // blau
  work: '#ef4444', // rot
  recovery_jog: '#93c5fd', // hellblau
  rest: '#9ca3af', // grau
  strides: '#f59e0b', // amber
  drills: '#a855f7', // lila
};

/** Deutsche Labels für Segment-Typen. */
export const SEGMENT_TYPE_LABELS: Record<string, string> = {
  warmup: 'Warm-up',
  cooldown: 'Cool-down',
  steady: 'Dauerlauf',
  work: 'Intervall',
  recovery_jog: 'Trabpause',
  rest: 'Pause',
  strides: 'Steigerung',
  drills: 'Lauf-ABC',
};

/** Optionen für Segment-Typ Dropdown. */
export const SEGMENT_TYPE_OPTIONS = Object.entries(SEGMENT_TYPE_LABELS).map(([value, label]) => ({
  value,
  label,
}));
