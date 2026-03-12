/**
 * Hook for exercise name autocomplete with click-outside dismissal.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import type { ExerciseCategory } from '@/api/session-templates';

const CATEGORY_MAP: Record<string, ExerciseCategory> = {
  push: 'push',
  pull: 'pull',
  legs: 'legs',
  core: 'core',
  cardio: 'cardio',
};

export function useExerciseSuggestions(
  shouldLoad: boolean,
  updateExercise: (id: string, updates: { name: string; category: ExerciseCategory }) => void,
) {
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!shouldLoad) return;
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
  }, [shouldLoad]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getFilteredSuggestions = useCallback(
    (query: string): Exercise[] => {
      if (!query.trim()) return libraryExercises.slice(0, 10);
      const lower = query.toLowerCase();
      return libraryExercises.filter((ex) => ex.name.toLowerCase().includes(lower)).slice(0, 8);
    },
    [libraryExercises],
  );

  const selectSuggestion = useCallback(
    (exerciseId: string, exercise: Exercise) => {
      updateExercise(exerciseId, {
        name: exercise.name,
        category: CATEGORY_MAP[exercise.category] ?? 'push',
      });
      setShowSuggestions(null);
    },
    [updateExercise],
  );

  return {
    showSuggestions,
    setShowSuggestions,
    suggestionsRef,
    getFilteredSuggestions,
    selectSuggestion,
  };
}
