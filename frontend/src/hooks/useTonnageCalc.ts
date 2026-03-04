import { useMemo } from 'react';
import type { ExerciseInput } from '@/api/strength';

/**
 * Calculate total tonnage for a list of exercises.
 * Excludes sets with status "skipped".
 */
export function calculateTonnage(exercises: ExerciseInput[]): number {
  let tonnage = 0;
  for (const ex of exercises) {
    for (const s of ex.sets) {
      if (s.status !== 'skipped') {
        tonnage += s.reps * s.weight_kg;
      }
    }
  }
  return Math.round(tonnage * 10) / 10;
}

/**
 * Calculate tonnage per exercise (by index).
 * Excludes sets with status "skipped".
 */
export function calculatePerExerciseTonnage(exercises: ExerciseInput[]): Map<number, number> {
  const map = new Map<number, number>();
  for (let i = 0; i < exercises.length; i++) {
    let tonnage = 0;
    for (const s of exercises[i].sets) {
      if (s.status !== 'skipped') {
        tonnage += s.reps * s.weight_kg;
      }
    }
    map.set(i, Math.round(tonnage * 10) / 10);
  }
  return map;
}

/**
 * Format tonnage for display: >= 1000 → "1.2t", else "850kg".
 */
export function formatTonnage(kg: number): { value: string; unit: string } {
  if (kg >= 1000) {
    return { value: (kg / 1000).toFixed(1), unit: 't' };
  }
  return { value: String(Math.round(kg)), unit: 'kg' };
}

/**
 * React hook that memoizes tonnage calculations.
 */
export function useTonnageCalc(exercises: ExerciseInput[]) {
  return useMemo(() => {
    const total = calculateTonnage(exercises);
    const perExercise = calculatePerExerciseTonnage(exercises);
    const formatted = formatTonnage(total);

    let totalSets = 0;
    for (const ex of exercises) {
      totalSets += ex.sets.length;
    }

    return { total, perExercise, formatted, exerciseCount: exercises.length, setCount: totalSets };
  }, [exercises]);
}
