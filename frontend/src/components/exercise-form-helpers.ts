/**
 * Shared Types und Helpers für das Übungs-Formular.
 * Wird von ExerciseFormSection, StrengthSession und StrengthExercisesEditor verwendet.
 */
import type { ExerciseCategory, SetStatus, SetType } from '@/api/strength';

// --- Types ---

export interface SetForm {
  id: string;
  type: SetType;
  reps?: number;
  weight_kg?: number;
  duration_sec?: number;
  distance_m?: number;
  status: SetStatus;
}

export interface ExerciseForm {
  id: string;
  name: string;
  category: ExerciseCategory;
  setType: SetType;
  sets: SetForm[];
}

// --- Helpers ---

let nextId = 0;
export function genId(prefix = 'ex'): string {
  return `${prefix}-${++nextId}-${Date.now()}`;
}

export function createDefaultSet(setType: SetType = 'weight_reps'): SetForm {
  const set: SetForm = { id: genId('set'), type: setType, status: 'completed' };
  // Set sensible defaults based on type
  if (
    setType === 'weight_reps' ||
    setType === 'weighted_bodyweight' ||
    setType === 'assisted_bodyweight'
  ) {
    set.reps = 10;
    set.weight_kg = 0;
  } else if (setType === 'bodyweight_reps') {
    set.reps = 10;
  } else if (setType === 'duration') {
    set.duration_sec = 0;
  } else if (setType === 'weight_duration') {
    set.weight_kg = 0;
    set.duration_sec = 0;
  } else if (setType === 'distance_duration') {
    set.duration_sec = 0;
    set.distance_m = 0;
  } else if (setType === 'weight_distance') {
    set.weight_kg = 0;
    set.distance_m = 0;
  }
  return set;
}

export function createDefaultExercise(): ExerciseForm {
  return {
    id: genId('ex'),
    name: '',
    category: 'push',
    setType: 'weight_reps',
    sets: [createDefaultSet('weight_reps')],
  };
}
