/**
 * Segment presets per run type.
 * Applied when the user changes the run type to pre-populate
 * a typical segment structure (e.g., warm-up + work + cool-down).
 */
import type { Segment } from '../api/segment';
import { createEmptySegment } from '../api/segment';
import type { SessionType } from '../constants/taxonomy';

type PresetDef = Array<{
  segment_type: Segment['segment_type'];
  target_duration_minutes: number;
  repeats?: number;
}>;

const PRESET_DEFS: Record<SessionType, PresetDef> = {
  easy: [{ segment_type: 'steady', target_duration_minutes: 40 }],
  recovery: [{ segment_type: 'steady', target_duration_minutes: 30 }],
  long_run: [{ segment_type: 'steady', target_duration_minutes: 90 }],
  race: [{ segment_type: 'steady', target_duration_minutes: 60 }],

  tempo: [
    { segment_type: 'warmup', target_duration_minutes: 10 },
    { segment_type: 'steady', target_duration_minutes: 20 },
    { segment_type: 'cooldown', target_duration_minutes: 10 },
  ],

  intervals: [
    { segment_type: 'warmup', target_duration_minutes: 10 },
    { segment_type: 'work', target_duration_minutes: 3, repeats: 4 },
    { segment_type: 'recovery_jog', target_duration_minutes: 2, repeats: 4 },
    { segment_type: 'cooldown', target_duration_minutes: 5 },
  ],

  progression: [
    { segment_type: 'warmup', target_duration_minutes: 10 },
    { segment_type: 'steady', target_duration_minutes: 15 },
    { segment_type: 'steady', target_duration_minutes: 10 },
    { segment_type: 'cooldown', target_duration_minutes: 5 },
  ],

  fartlek: [
    { segment_type: 'warmup', target_duration_minutes: 10 },
    { segment_type: 'steady', target_duration_minutes: 20 },
    { segment_type: 'cooldown', target_duration_minutes: 5 },
  ],

  repetitions: [
    { segment_type: 'warmup', target_duration_minutes: 10 },
    { segment_type: 'work', target_duration_minutes: 1, repeats: 6 },
    { segment_type: 'recovery_jog', target_duration_minutes: 3, repeats: 6 },
    { segment_type: 'cooldown', target_duration_minutes: 5 },
  ],
};

/**
 * Get preset segments for a given run type.
 * Returns fresh Segment objects with correct positions.
 */
export function getPresetSegments(runType: SessionType): Segment[] {
  const defs = PRESET_DEFS[runType];
  return defs.map((def, i) =>
    createEmptySegment(i, {
      segment_type: def.segment_type,
      target_duration_minutes: def.target_duration_minutes,
      repeats: def.repeats ?? 1,
    }),
  );
}

/**
 * Check if segments contain meaningful user data.
 * A single default segment (steady/work) with no values is considered "empty".
 */
export function hasSegmentData(segments: Segment[] | undefined | null): boolean {
  if (!segments || segments.length === 0) return false;

  // More than one segment → user has customized
  if (segments.length > 1) return true;

  const seg = segments[0];

  // Non-default type → user has customized
  if (seg.segment_type !== 'steady' && seg.segment_type !== 'work') return true;

  // Any target value set → has data
  if (seg.target_duration_minutes != null) return true;
  if (seg.target_distance_km != null) return true;
  if (seg.target_pace_min != null) return true;
  if (seg.target_pace_max != null) return true;
  if (seg.target_hr_min != null) return true;
  if (seg.target_hr_max != null) return true;
  if (seg.notes != null && seg.notes !== '') return true;
  if (seg.repeats > 1) return true;

  return false;
}
