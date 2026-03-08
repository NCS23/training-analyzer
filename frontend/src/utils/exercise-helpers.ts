/**
 * Shared utilities for exercise editing — used by both
 * `SessionTemplateEditor` (full-page) and `StrengthExerciseEditor` (inline).
 */
import type { ExerciseCategory, ExerciseType, TemplateExercise } from '@/api/session-templates';

// --- Internal form state ---

export interface ExerciseForm {
  id: string;
  name: string;
  category: ExerciseCategory;
  sets: number;
  reps: number;
  weight_kg: number;
  exercise_type: ExerciseType;
  notes: string;
  collapsed: boolean;
}

// --- Constants ---

export const CATEGORY_OPTIONS: { value: ExerciseCategory; label: string }[] = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

export const CATEGORY_LABELS: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Lauf-ABC',
};

export const EXERCISE_TYPE_OPTIONS: { value: ExerciseType; label: string }[] = [
  { value: 'kraft', label: 'Kraft' },
  { value: 'mobilitaet', label: 'Mobilität' },
  { value: 'dehnung', label: 'Dehnung' },
];

// --- ID generation ---

let nextId = 0;
export function genId(): string {
  return `ex-${++nextId}-${Date.now()}`;
}

// --- Converters ---

export function createDefaultExercise(): ExerciseForm {
  return {
    id: genId(),
    name: '',
    category: 'push',
    sets: 3,
    reps: 10,
    weight_kg: 0,
    exercise_type: 'kraft',
    notes: '',
    collapsed: false,
  };
}

export function exerciseFormToApi(ex: ExerciseForm): TemplateExercise {
  return {
    name: ex.name.trim(),
    category: ex.category,
    sets: ex.sets,
    reps: ex.reps,
    weight_kg: ex.weight_kg > 0 ? ex.weight_kg : null,
    exercise_type: ex.exercise_type,
    notes: ex.notes.trim() || null,
  };
}

export function apiExerciseToForm(ex: TemplateExercise): ExerciseForm {
  return {
    id: genId(),
    name: ex.name,
    category: ex.category,
    sets: ex.sets,
    reps: ex.reps,
    weight_kg: ex.weight_kg ?? 0,
    exercise_type: ex.exercise_type,
    notes: ex.notes ?? '',
    collapsed: true,
  };
}
