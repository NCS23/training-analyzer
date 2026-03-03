/**
 * Unified Segment Model — TypeScript mirror of backend Segment.
 *
 * Single interface for both planned (Soll) and actual (Ist) run segments.
 * Part of Epic #133 (Einheitliches Segment-Modell).
 */

export type SegmentType =
  | 'warmup'
  | 'cooldown'
  | 'steady'
  | 'work'
  | 'recovery_jog'
  | 'rest'
  | 'strides'
  | 'drills';

export interface Segment {
  // Identity
  position: number;
  segment_type: SegmentType;

  // Planning (Soll) — filled for templates + weekly plan
  target_duration_minutes: number | null;
  target_distance_km: number | null;
  target_pace_min: string | null;
  target_pace_max: string | null;
  target_hr_min: number | null;
  target_hr_max: number | null;
  repeats: number;

  // Enrichment — free-text notes and optional exercise reference
  notes: string | null;
  exercise_name: string | null;

  // Actual (Ist) — filled after session upload
  actual_duration_seconds: number | null;
  actual_distance_km: number | null;
  actual_pace_formatted: string | null;
  actual_hr_avg: number | null;
  actual_hr_max: number | null;
  actual_hr_min: number | null;
  actual_cadence_spm: number | null;

  // Timing (for UI visualization, Ist only)
  start_seconds: number | null;
  end_seconds: number | null;

  // Classification (Ist only)
  suggested_type: string | null;
  confidence: string | null;
  user_override: string | null;
}

/**
 * Create an empty Segment with all Ist fields set to null.
 * Used by the segment editor to create new segments.
 */
export function createEmptySegment(position: number = 0, overrides?: Partial<Segment>): Segment {
  return {
    position,
    segment_type: 'work',
    target_duration_minutes: null,
    target_distance_km: null,
    target_pace_min: null,
    target_pace_max: null,
    target_hr_min: null,
    target_hr_max: null,
    repeats: 1,
    notes: null,
    exercise_name: null,
    actual_duration_seconds: null,
    actual_distance_km: null,
    actual_pace_formatted: null,
    actual_hr_avg: null,
    actual_hr_max: null,
    actual_hr_min: null,
    actual_cadence_spm: null,
    start_seconds: null,
    end_seconds: null,
    suggested_type: null,
    confidence: null,
    user_override: null,
    ...overrides,
  };
}

/**
 * Format a compact summary of work segments (e.g., "4×3′").
 * Returns null if no work segments found.
 */
export function formatSegmentSummary(segments: Segment[]): string | null {
  const workSegs = segments.filter((s) => s.segment_type === 'work');
  if (workSegs.length === 0) return null;
  const first = workSegs[0];
  let target = '';
  if (first.target_distance_km) {
    target =
      first.target_distance_km >= 1
        ? `${first.target_distance_km} km`
        : `${first.target_distance_km * 1000}m`;
  } else if (first.target_duration_minutes) {
    target = `${first.target_duration_minutes}′`;
  }
  return `${workSegs.length}×${target}`;
}

/**
 * Expand a segment with repeats > 1 into individual segments.
 * E.g., 4×3min work → 4 work + 3 recovery_jog = 7 segments.
 */
export function expandSegments(segments: Segment[]): Segment[] {
  const result: Segment[] = [];
  for (const seg of segments) {
    if (seg.repeats <= 1) {
      result.push({ ...seg, repeats: 1 });
    } else {
      for (let i = 0; i < seg.repeats; i++) {
        result.push({
          ...seg,
          position: seg.position + i * 2,
          repeats: 1,
        });
        if (i < seg.repeats - 1) {
          result.push(
            createEmptySegment(seg.position + i * 2 + 1, { segment_type: 'recovery_jog' }),
          );
        }
      }
    }
  }
  return result;
}
