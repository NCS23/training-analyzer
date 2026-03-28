/**
 * Segment-Tabelle mit Inline-Editing für Route-Segmente.
 * Erlaubt Typ-Auswahl, Pace/HR-Ziele pro Segment.
 */

import { Button, Input, Select, Badge } from '@nordlig/components';
import { Trash2, Plus } from 'lucide-react';
import { SEGMENT_TYPE_COLORS, SEGMENT_TYPE_OPTIONS } from '@/constants/segmentColors';
import type { RouteSegment } from '@/api/routes';

interface SegmentTableProps {
  segments: RouteSegment[];
  totalDistanceKm: number;
  onUpdate: (index: number, segment: RouteSegment) => void;
  onDelete: (index: number) => void;
  onAdd: () => void;
  activeSegment?: number | null;
  onSegmentClick?: (index: number) => void;
}

function SegmentRow({
  segment,
  index,
  onUpdate,
  onDelete,
  isActive,
  onClick,
}: {
  segment: RouteSegment;
  index: number;
  onUpdate: (index: number, seg: RouteSegment) => void;
  onDelete: (index: number) => void;
  isActive: boolean;
  onClick: () => void;
}) {
  const color = SEGMENT_TYPE_COLORS[segment.segment_type] ?? '#9ca3af';

  return (
    <div
      onClick={onClick}
      className={`flex flex-col sm:flex-row sm:items-center gap-2 p-3 rounded-[var(--radius-component-sm)] border cursor-pointer transition-colors motion-reduce:transition-none ${
        isActive
          ? 'border-[var(--color-border-focus)] bg-[var(--color-bg-subtle)]'
          : 'border-[var(--color-border-default)]'
      }`}
    >
      {/* Farb-Indikator + Typ */}
      <div className="flex items-center gap-2 min-w-[140px]">
        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
        <Select
          options={SEGMENT_TYPE_OPTIONS}
          value={segment.segment_type}
          onChange={(val) => {
            if (val) onUpdate(index, { ...segment, segment_type: val });
          }}
          className="text-sm flex-1"
        />
      </div>

      {/* Distanz */}
      <Badge variant="neutral" size="sm" className="flex-shrink-0">
        {segment.start_km.toFixed(1)}–{segment.end_km.toFixed(1)} km
      </Badge>

      {/* Pace */}
      <div className="flex items-center gap-1">
        <Input
          placeholder="min"
          value={segment.target_pace_min ?? ''}
          onChange={(e) => onUpdate(index, { ...segment, target_pace_min: e.target.value || null })}
          className="w-16 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">–</span>
        <Input
          placeholder="max"
          value={segment.target_pace_max ?? ''}
          onChange={(e) => onUpdate(index, { ...segment, target_pace_max: e.target.value || null })}
          className="w-16 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">/km</span>
      </div>

      {/* HR */}
      <div className="flex items-center gap-1">
        <Input
          placeholder="HR"
          type="number"
          value={segment.target_hr_min ?? ''}
          onChange={(e) =>
            onUpdate(index, {
              ...segment,
              target_hr_min: e.target.value ? Number(e.target.value) : null,
            })
          }
          className="w-14 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">–</span>
        <Input
          placeholder="HR"
          type="number"
          value={segment.target_hr_max ?? ''}
          onChange={(e) =>
            onUpdate(index, {
              ...segment,
              target_hr_max: e.target.value ? Number(e.target.value) : null,
            })
          }
          className="w-14 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">bpm</span>
      </div>

      {/* Delete */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(index);
        }}
        className="p-1.5 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-subtle)] min-w-[44px] min-h-[44px] flex items-center justify-center flex-shrink-0"
      >
        <Trash2 className="w-4 h-4 text-[var(--color-text-muted)]" />
      </button>
    </div>
  );
}

export function SegmentTable({
  segments,
  totalDistanceKm,
  onUpdate,
  onDelete,
  onAdd,
  activeSegment,
  onSegmentClick,
}: SegmentTableProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-[var(--color-text-base)]">
          Segmente ({segments.length})
        </h3>
        <Button variant="secondary" size="sm" onClick={onAdd} disabled={totalDistanceKm <= 0}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          Segment
        </Button>
      </div>

      {segments.length === 0 && (
        <p className="text-xs text-[var(--color-text-muted)] py-4 text-center">
          Noch keine Segmente. Klicke „Segment" um die Route aufzuteilen.
        </p>
      )}

      <div className="space-y-1.5">
        {segments.map((seg, i) => (
          <SegmentRow
            key={i}
            segment={seg}
            index={i}
            onUpdate={onUpdate}
            onDelete={onDelete}
            isActive={activeSegment === i}
            onClick={() => onSegmentClick?.(i)}
          />
        ))}
      </div>
    </div>
  );
}
