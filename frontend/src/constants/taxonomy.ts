/** Canonical session type and segment type definitions.
 *  Single source of truth for the training taxonomy on the frontend.
 */

export const SESSION_TYPES = [
  'recovery',
  'easy',
  'long_run',
  'progression',
  'tempo',
  'intervals',
  'repetitions',
  'fartlek',
  'race',
] as const;

export type SessionType = (typeof SESSION_TYPES)[number];

export const SEGMENT_TYPES = [
  'warmup',
  'cooldown',
  'steady',
  'work',
  'recovery_jog',
  'rest',
  'strides',
  'drills',
] as const;

export type SegmentType = (typeof SEGMENT_TYPES)[number];

export const EXCLUDED_SEGMENT_TYPES = new Set<SegmentType>(['warmup', 'cooldown', 'rest']);
