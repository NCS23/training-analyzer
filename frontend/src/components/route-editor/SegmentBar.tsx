/**
 * Farbcodierte Segment-Leiste — zeigt Segmente proportional zur Distanz.
 * Klickbar für Segment-Auswahl.
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
      <div
        className="flex h-5 rounded-[var(--radius-component-sm)] overflow-hidden"
        role="group"
        aria-label="Segment-Übersicht"
      >
        {segments.map((seg, i) => {
          const width = ((seg.end_km - seg.start_km) / totalDistanceKm) * 100;
          const color = SEGMENT_TYPE_COLORS[seg.segment_type] ?? '#9ca3af';
          const isActive = activeSegment === i;
          const label = SEGMENT_TYPE_LABELS[seg.segment_type] ?? seg.segment_type;

          return (
            <div
              key={i}
              role="button"
              tabIndex={0}
              onClick={() => onSegmentClick?.(i)}
              onKeyDown={(e) => e.key === 'Enter' && onSegmentClick?.(i)}
              className="relative transition-opacity motion-reduce:transition-none min-w-[2px] cursor-pointer"
              style={{
                width: `${width}%`,
                backgroundColor: color,
                opacity: isActive ? 1 : 0.75,
              }}
              title={`${label}: ${seg.start_km.toFixed(1)}–${seg.end_km.toFixed(1)} km`}
              aria-label={`${label}: ${seg.start_km.toFixed(1)} bis ${seg.end_km.toFixed(1)} km`}
              aria-pressed={isActive}
            >
              {width > 12 && (
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-medium text-[var(--color-text-on-primary)] select-none">
                  {label.slice(0, 4)}
                </span>
              )}
            </div>
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
