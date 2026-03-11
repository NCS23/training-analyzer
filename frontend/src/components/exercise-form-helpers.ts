/**
 * Shared Types und Helpers für das Übungs-Formular.
 * Wird von ExerciseFormSection, StrengthSession und StrengthExercisesEditor verwendet.
 */
import type { ExerciseCategory, SetStatus } from '@/api/strength';

// --- Types ---

export interface SetForm {
  id: string;
  reps: number;
  weight_kg: number;
  status: SetStatus;
}

export interface ExerciseForm {
  id: string;
  name: string;
  category: ExerciseCategory;
  sets: SetForm[];
}

// --- Helpers ---

let nextId = 0;
export function genId(prefix = 'ex'): string {
  return `${prefix}-${++nextId}-${Date.now()}`;
}

export function createDefaultSet(): SetForm {
  return { id: genId('set'), reps: 10, weight_kg: 0, status: 'completed' };
}

export function createDefaultExercise(): ExerciseForm {
  return { id: genId('ex'), name: '', category: 'push', sets: [createDefaultSet()] };
}
