/**
 * Reusable hook for template exercise list CRUD + reordering.
 * Used by SessionTemplateEditor and Upload pages.
 */
import { useState, useCallback } from 'react';
import type { ExerciseForm } from '@/utils/exercise-helpers';
import { createDefaultExercise } from '@/utils/exercise-helpers';

export function useExerciseListEditor(initial?: ExerciseForm[]) {
  const [exercises, setExercises] = useState<ExerciseForm[]>(initial ?? [createDefaultExercise()]);

  const updateExercise = useCallback((exerciseId: string, updates: Partial<ExerciseForm>) => {
    setExercises((prev) => prev.map((ex) => (ex.id === exerciseId ? { ...ex, ...updates } : ex)));
  }, []);

  const removeExercise = useCallback((exerciseId: string) => {
    setExercises((prev) => {
      const filtered = prev.filter((ex) => ex.id !== exerciseId);
      return filtered.length === 0 ? [createDefaultExercise()] : filtered;
    });
  }, []);

  const addExercise = useCallback(() => {
    setExercises((prev) => [...prev, createDefaultExercise()]);
  }, []);

  const moveExercise = useCallback((index: number, direction: -1 | 1) => {
    setExercises((prev) => {
      const newIndex = index + direction;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[newIndex]] = [next[newIndex], next[index]];
      return next;
    });
  }, []);

  return {
    exercises,
    setExercises,
    updateExercise,
    removeExercise,
    addExercise,
    moveExercise,
  };
}
