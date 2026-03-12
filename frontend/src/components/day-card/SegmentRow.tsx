import type { Segment } from '@/api/segment';
import { lapTypeLabels } from '@/constants/training';

export function SegmentRow({ segment }: { segment: Segment }) {
  const label = lapTypeLabels[segment.segment_type] ?? segment.segment_type;
  const parts: string[] = [];
  if (segment.target_duration_minutes) parts.push(`${segment.target_duration_minutes} min`);
  if (segment.target_distance_km) {
    parts.push(
      segment.target_distance_km >= 1
        ? `${segment.target_distance_km} km`
        : `${segment.target_distance_km * 1000}m`,
    );
  }
  if (segment.target_pace_min) {
    parts.push(
      segment.target_pace_max
        ? `${segment.target_pace_min}–${segment.target_pace_max}/km`
        : `${segment.target_pace_min}/km`,
    );
  }
  if (segment.target_hr_min || segment.target_hr_max) {
    parts.push(`${[segment.target_hr_min, segment.target_hr_max].filter(Boolean).join('–')} bpm`);
  }

  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs rounded-[var(--radius-component-sm)] bg-[var(--color-bg-muted)] px-2 py-1">
      {segment.repeats > 1 && (
        <span className="text-[var(--color-text-muted)] font-medium">{segment.repeats}×</span>
      )}
      <span className="font-medium text-[var(--color-text-base)]">{label}</span>
      {segment.exercise_name && (
        <span className="italic text-[var(--color-text-muted)]">{segment.exercise_name}</span>
      )}
      {parts.length > 0 && (
        <span className="text-[var(--color-text-muted)]">{parts.join(' · ')}</span>
      )}
      {segment.notes && (
        <span className="text-[10px] text-[var(--color-text-muted)] basis-full">
          {segment.notes}
        </span>
      )}
    </div>
  );
}
