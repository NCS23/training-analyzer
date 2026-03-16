import { useMemo } from 'react';
import type { ExerciseInput } from '@/api/strength';

/**
 * Calculate total tonnage for a list of exercises.
 * Excludes sets with status "skipped". Only counts sets with both reps and weight.
 */
export function calculateTonnage(exercises: ExerciseInput[]): number {
  let tonnage = 0;
  for (const ex of exercises) {
    for (const s of ex.sets) {
      if (s.status !== 'skipped') {
        tonnage += (s.reps ?? 0) * (s.weight_kg ?? 0);
      }
    }
  }
  return Math.round(tonnage * 10) / 10;
}

/**
 * Calculate total reps (for bodyweight exercises without weight).
 */
export function calculateTotalReps(exercises: ExerciseInput[]): number {
  let total = 0;
  for (const ex of exercises) {
    for (const s of ex.sets) {
      if (s.status !== 'skipped') {
        total += s.reps ?? 0;
      }
    }
  }
  return total;
}

/**
 * Calculate total duration in seconds (for time-based exercises).
 */
export function calculateTotalDuration(exercises: ExerciseInput[]): number {
  let total = 0;
  for (const ex of exercises) {
    for (const s of ex.sets) {
      if (s.status !== 'skipped') {
        total += s.duration_sec ?? 0;
      }
    }
  }
  return total;
}

/**
 * Calculate total distance in meters (for distance-based exercises).
 */
export function calculateTotalDistance(exercises: ExerciseInput[]): number {
  let total = 0;
  for (const ex of exercises) {
    for (const s of ex.sets) {
      if (s.status !== 'skipped') {
        total += s.distance_m ?? 0;
      }
    }
  }
  return total;
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
        tonnage += (s.reps ?? 0) * (s.weight_kg ?? 0);
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
    const totalReps = calculateTotalReps(exercises);
    const totalDuration = calculateTotalDuration(exercises);
    const totalDistance = calculateTotalDistance(exercises);
    const perExercise = calculatePerExerciseTonnage(exercises);
    const formatted = formatTonnage(total);

    let totalSets = 0;
    for (const ex of exercises) {
      totalSets += ex.sets.length;
    }

    return {
      total,
      totalReps,
      totalDuration,
      totalDistance,
      perExercise,
      formatted,
      exerciseCount: exercises.length,
      setCount: totalSets,
    };
  }, [exercises]);
}
