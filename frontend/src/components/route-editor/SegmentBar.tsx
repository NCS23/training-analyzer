/**
 * Farbcodierte Segment-Leiste unter der Karte.
 * Zeigt alle Segmente proportional zur Distanz als farbige Balken.
 */

import { SEGMENT_TYPE_COLORS, SEGMENT_TYPE_LABELS } from '@/constants/segmentColors';
import type { RouteSegment } from '@/api/routes';

interface SegmentBarProps {
  segments: RouteSegment[];
  totalDistanceKm: number;
  onSegmentClick?: (index: number) => void;
  activeSegment?: number | null;
}

export function SegmentBar({
  segments,
  totalDistanceKm,
  onSegmentClick,
  activeSegment,
}: SegmentBarProps) {
  if (segments.length === 0 || totalDistanceKm <= 0) return null;

  return (
    <div className="space-y-1.5">
      <div className="flex h-6 rounded-[var(--radius-component-sm)] overflow-hidden border border-[var(--color-border-default)]">
        {segments.map((seg, i) => {
          const width = ((seg.end_km - seg.start_km) / totalDistanceKm) * 100;
          const color = SEGMENT_TYPE_COLORS[seg.segment_type] ?? '#9ca3af';
          const isActive = activeSegment === i;

          return (
            <button
              key={i}
              onClick={() => onSegmentClick?.(i)}
              className="relative transition-opacity motion-reduce:transition-none min-w-[2px]"
              style={{
                width: `${width}%`,
                backgroundColor: color,
                opacity: isActive ? 1 : 0.7,
              }}
              title={`${SEGMENT_TYPE_LABELS[seg.segment_type] ?? seg.segment_type}: ${seg.start_km}–${seg.end_km} km`}
            >
              {width > 10 && (
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-[var(--color-text-on-primary)]">
                  {SEGMENT_TYPE_LABELS[seg.segment_type]?.slice(0, 4) ?? ''}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div className="flex justify-between text-[10px] text-[var(--color-text-muted)]">
        <span>0 km</span>
        <span>{totalDistanceKm.toFixed(1)} km</span>
      </div>
    </div>
  );
}
