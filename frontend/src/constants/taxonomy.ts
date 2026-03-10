/** Canonical training taxonomy definitions.
 *  Single source of truth for session types, segment types, and phase focus tags.
 */

import type { PhaseType } from '@/api/training-plans';

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

// Phase focus tags — trainingswissenschaftlich fundierter Katalog
export const PHASE_FOCUS_TAGS: { value: string; label: string }[] = [
  { value: 'aerobic_base', label: 'Aerobe Grundlage' },
  { value: 'structural_adaptation', label: 'Strukturanpassung' },
  { value: 'running_economy', label: 'Laufökonomie' },
  { value: 'injury_prevention', label: 'Verletzungsprävention' },
  { value: 'lactate_threshold', label: 'Laktatschwelle' },
  { value: 'tempo_hardness', label: 'Tempohärte' },
  { value: 'specific_strength', label: 'Spezifische Kraft' },
  { value: 'race_pace_intro', label: 'Wettkampftempo-Einführung' },
  { value: 'vo2max', label: 'VO2max' },
  { value: 'race_pace', label: 'Wettkampftempo' },
  { value: 'race_tactics', label: 'Renntaktik' },
  { value: 'mental_toughness', label: 'Mentale Härte' },
  { value: 'supercompensation', label: 'Superkompensation' },
  { value: 'fatigue_reduction', label: 'Ermüdungsabbau' },
  { value: 'mental_preparation', label: 'Mentale Vorbereitung' },
  { value: 'race_preparation', label: 'Wettkampfvorbereitung' },
  { value: 'regeneration', label: 'Regeneration' },
  { value: 'mobility', label: 'Mobilität' },
  { value: 'overtraining_prevention', label: 'Übertrainings-Prävention' },
];

// Lookup map for focus tag value → label (with fallback for custom tags)
export function getFocusLabel(value: string): string {
  return PHASE_FOCUS_TAGS.find((t) => t.value === value)?.label ?? value;
}

// Reverse lookup: label → canonical key (for migrating legacy data stored as German labels)
const _labelToKey = new Map<string, string>([
  // Canonical catalog labels
  ...PHASE_FOCUS_TAGS.map((t) => [t.label.toLowerCase(), t.value] as [string, string]),
  // YAML-imported legacy labels (from plan generator / manual YAML files)
  ['grundlagenausdauer', 'aerobic_base'],
  ['formaufbau', 'structural_adaptation'],
  ['verletzungspraevention', 'injury_prevention'],
  ['verletzungsprävention', 'injury_prevention'],
  ['kraftstabilitaet', 'specific_strength'],
  ['kraftstabilität', 'specific_strength'],
  ['tempodauerlauf', 'tempo_hardness'],
  ['laufoekonomie', 'running_economy'],
  ['laufökonomie', 'running_economy'],
  ['mentale haerte', 'mental_toughness'],
  ['mentale härte', 'mental_toughness'],
  ['erholung', 'regeneration'],
  ['mentale frische', 'mental_preparation'],
]);
const _knownKeys = new Set(PHASE_FOCUS_TAGS.map((t) => t.value));

/** Normalize a focus value: if it's already a canonical key, keep it;
 *  if it's a German label (catalog or legacy YAML), convert to canonical key;
 *  otherwise pass through as-is. */
export function normalizeFocusKey(value: string): string {
  if (_knownKeys.has(value)) return value;
  return _labelToKey.get(value.toLowerCase()) ?? value;
}

// Default focus suggestions per phase type
export const PHASE_FOCUS_DEFAULTS: Record<PhaseType, { primary: string[]; secondary: string[] }> = {
  base: {
    primary: ['aerobic_base', 'structural_adaptation'],
    secondary: ['running_economy', 'injury_prevention'],
  },
  build: {
    primary: ['lactate_threshold', 'tempo_hardness'],
    secondary: ['specific_strength', 'race_pace_intro'],
  },
  peak: {
    primary: ['vo2max', 'race_pace'],
    secondary: ['race_tactics', 'mental_toughness'],
  },
  taper: {
    primary: ['supercompensation', 'fatigue_reduction'],
    secondary: ['mental_preparation', 'race_preparation'],
  },
  transition: {
    primary: ['regeneration', 'mobility'],
    secondary: ['overtraining_prevention'],
  },
};
