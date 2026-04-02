/**
 * Segment-Liste mit Inline-Editing für Route-Segmente.
 * Im readOnly-Modus: statische Darstellung ohne Edit-Controls.
 */

import { Button, Input, Select, Badge } from '@nordlig/components';
import { Trash2 } from 'lucide-react';
import {
  SEGMENT_TYPE_COLORS,
  SEGMENT_TYPE_LABELS,
  SEGMENT_TYPE_OPTIONS,
} from '@/constants/segmentColors';
import type { RouteSegment } from '@/api/routes';

interface SegmentTableProps {
  segments: RouteSegment[];
  totalDistanceKm: number;
  onUpdate: (index: number, segment: RouteSegment) => void;
  onDelete: (index: number) => void;
  onAdd: () => void;
  activeSegment?: number | null;
  onSegmentClick?: (index: number) => void;
  readOnly?: boolean;
}

// ---------------------------------------------------------------------------
// Read-only Zeile
// ---------------------------------------------------------------------------

function SegmentRowReadOnly({
  segment,
  isActive,
  onClick,
}: {
  segment: RouteSegment;
  isActive: boolean;
  onClick: () => void;
}) {
  const color = SEGMENT_TYPE_COLORS[segment.segment_type] ?? '#9ca3af';
  const label = SEGMENT_TYPE_LABELS[segment.segment_type] ?? segment.segment_type;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-component-sm)] border cursor-pointer transition-colors motion-reduce:transition-none ${
        isActive
          ? 'border-[var(--color-border-focus)] bg-[var(--color-bg-subtle)]'
          : 'border-[var(--color-border-default)]'
      }`}
    >
      <div
        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="text-sm font-medium text-[var(--color-text-base)] min-w-[100px]">
        {label}
      </span>
      <Badge variant="neutral" size="sm" className="flex-shrink-0">
        {segment.start_km.toFixed(1)}–{segment.end_km.toFixed(1)} km
      </Badge>
      {segment.target_pace_min && (
        <span className="text-xs text-[var(--color-text-muted)] ml-auto">
          {segment.target_pace_min}
          {segment.target_pace_max ? `–${segment.target_pace_max}` : ''} /km
        </span>
      )}
      {segment.target_hr_min && (
        <span className="text-xs text-[var(--color-text-muted)]">
          {segment.target_hr_min}
          {segment.target_hr_max ? `–${segment.target_hr_max}` : ''} bpm
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Edit-Zeile
// ---------------------------------------------------------------------------

// eslint-disable-next-line max-lines-per-function -- Segment-Zeile enthält Pace + HR + Typ-Felder
function SegmentRowEdit({
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
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ backgroundColor: color }}
        />
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

      {/* HR — type="text" mit inputMode="numeric" vermeidet native Browser-Spinner */}
      <div className="flex items-center gap-1">
        <Input
          placeholder="140"
          type="text"
          inputMode="numeric"
          value={segment.target_hr_min ?? ''}
          onChange={(e) => {
            const val = e.target.value.replace(/\D/g, '');
            onUpdate(index, { ...segment, target_hr_min: val ? Number(val) : null });
          }}
          className="w-14 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">–</span>
        <Input
          placeholder="160"
          type="text"
          inputMode="numeric"
          value={segment.target_hr_max ?? ''}
          onChange={(e) => {
            const val = e.target.value.replace(/\D/g, '');
            onUpdate(index, { ...segment, target_hr_max: val ? Number(val) : null });
          }}
          className="w-14 text-xs"
        />
        <span className="text-xs text-[var(--color-text-muted)]">bpm</span>
      </div>

      {/* Löschen */}
      <Button
        variant="ghost"
        size="sm"
        aria-label="Segment löschen"
        onClick={(e: React.MouseEvent) => {
          e.stopPropagation();
          onDelete(index);
        }}
        className="flex-shrink-0"
      >
        <Trash2 className="w-4 h-4 text-[var(--color-text-muted)]" />
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tabelle
// ---------------------------------------------------------------------------

export function SegmentTable({
  segments,
  totalDistanceKm,
  onUpdate,
  onDelete,
  onAdd,
  activeSegment,
  onSegmentClick,
  readOnly = false,
}: SegmentTableProps) {
  void totalDistanceKm; // wird vom Parent für Distanz-Berechnung genutzt
  void onAdd; // wird vom Parent (CardHeader) ausgelöst

  return (
    <div className="space-y-1.5">
      {segments.map((seg, i) =>
        readOnly ? (
          <SegmentRowReadOnly
            key={i}
            segment={seg}
            isActive={activeSegment === i}
            onClick={() => onSegmentClick?.(i)}
          />
        ) : (
          <SegmentRowEdit
            key={i}
            segment={seg}
            index={i}
            onUpdate={onUpdate}
            onDelete={onDelete}
            isActive={activeSegment === i}
            onClick={() => onSegmentClick?.(i)}
          />
        ),
      )}
    </div>
  );
}
