/**
 * Map legend overlay for pace/HR heat map visualization.
 * Rendered as a React component (not L.Control) for Nordlig DS compatibility.
 */
import type { HRZoneBoundary } from '@/utils/colorScale';
import { paceColor } from '@/utils/colorScale';

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

export interface MapLegendProps {
  mode: 'pace' | 'hr';
  /** For pace mode: fastest pace in session (min/km). */
  minPace?: number;
  /** For pace mode: slowest pace in session (min/km). */
  maxPace?: number;
  /** For HR mode: zone boundaries with colors. */
  zones?: HRZoneBoundary[];
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatPace(paceMinPerKm: number): string {
  const mins = Math.floor(paceMinPerKm);
  const secs = Math.round((paceMinPerKm - mins) * 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/** Build a CSS linear-gradient from the pace color scale. */
function paceGradient(): string {
  const stops = 10;
  const colors: string[] = [];
  for (let i = 0; i <= stops; i++) {
    colors.push(paceColor(i / stops));
  }
  return `linear-gradient(to right, ${colors.join(', ')})`;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function MapLegend({ mode, minPace, maxPace, zones }: MapLegendProps) {
  if (mode === 'pace') {
    if (minPace == null || maxPace == null) return null;
    return (
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <span className="tabular-nums">{formatPace(minPace)}</span>
        <div
          className="h-2 flex-1 min-w-[80px] rounded-full"
          style={{ background: paceGradient() }}
          aria-label={`Pace: ${formatPace(minPace)} bis ${formatPace(maxPace)} /km`}
        />
        <span className="tabular-nums">{formatPace(maxPace)}</span>
        <span>/km</span>
      </div>
    );
  }

  // HR mode
  if (!zones || zones.length === 0) return null;
  return (
    <div
      className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] flex-wrap"
      aria-label="Herzfrequenz-Zonen Legende"
    >
      {zones.map((z) => (
        <span key={z.zone} className="inline-flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-[var(--radius-sm)] shrink-0" style={{ backgroundColor: z.color }} />
          <span className="tabular-nums">
            Z{z.zone} {z.lowerBpm}–{z.upperBpm}
          </span>
        </span>
      ))}
      <span>bpm</span>
    </div>
  );
}
