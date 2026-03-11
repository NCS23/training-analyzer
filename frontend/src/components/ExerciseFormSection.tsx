/**
 * Shared Übungs-Formular-Section für Erstellen und Bearbeiten.
 * Wird identisch in StrengthSession.tsx und StrengthExercisesEditor.tsx verwendet.
 * Enthält: Exercise-Name mit DB-Autocomplete, Category-Select, Set-Rows, CRUD-Buttons.
 */
import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { Button, Input, NumberInput, Select } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import {
  calculateTonnage,
  calculatePerExerciseTonnage,
  formatTonnage,
} from '@/hooks/useTonnageCalc';
import type { ExerciseInput } from '@/api/strength';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import type { ExerciseCategory, SetStatus } from '@/api/strength';
import { genId, createDefaultSet, createDefaultExercise } from './exercise-form-helpers';
import type { ExerciseForm, SetForm } from './exercise-form-helpers';

// --- Constants ---

const CATEGORY_SELECT_OPTIONS = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

const STATUS_SELECT_OPTIONS = [
  { value: 'completed', label: 'Fertig' },
  { value: 'reduced', label: 'Reduziert' },
  { value: 'skipped', label: 'Übersprungen' },
];

// --- Props ---

interface ExerciseFormSectionProps {
  exercises: ExerciseForm[];
  setExercises: React.Dispatch<React.SetStateAction<ExerciseForm[]>>;
  /** Hide the built-in tonnage summary (e.g. when the parent has its own). */
  hideTonnageSummary?: boolean;
}

// --- Component ---

export function ExerciseFormSection({
  exercises,
  setExercises,
  hideTonnageSummary = false,
}: ExerciseFormSectionProps) {
  // Library exercises for autocomplete
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [activeAutocomplete, setActiveAutocomplete] = useState<string | null>(null);
  const autocompleteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
  }, []);

  // Close autocomplete on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (autocompleteRef.current && !autocompleteRef.current.contains(e.target as Node)) {
        setActiveAutocomplete(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- Exercise CRUD ---

  const updateExercise = useCallback(
    (exerciseId: string, updates: Partial<ExerciseForm>) => {
      setExercises((prev) => prev.map((ex) => (ex.id === exerciseId ? { ...ex, ...updates } : ex)));
    },
    [setExercises],
  );

  const removeExercise = useCallback(
    (exerciseId: string) => {
      setExercises((prev) => {
        const filtered = prev.filter((ex) => ex.id !== exerciseId);
        return filtered.length === 0 ? [createDefaultExercise()] : filtered;
      });
    },
    [setExercises],
  );

  const addExercise = useCallback(() => {
    setExercises((prev) => [...prev, createDefaultExercise()]);
  }, [setExercises]);

  // --- Set CRUD ---

  const updateSet = useCallback(
    (exerciseId: string, setId: string, updates: Partial<SetForm>) => {
      setExercises((prev) =>
        prev.map((ex) =>
          ex.id === exerciseId
            ? { ...ex, sets: ex.sets.map((s) => (s.id === setId ? { ...s, ...updates } : s)) }
            : ex,
        ),
      );
    },
    [setExercises],
  );

  const addSet = useCallback(
    (exerciseId: string) => {
      setExercises((prev) =>
        prev.map((ex) => {
          if (ex.id !== exerciseId) return ex;
          const lastSet = ex.sets[ex.sets.length - 1];
          const newSet: SetForm = lastSet
            ? {
                id: genId('set'),
                reps: lastSet.reps,
                weight_kg: lastSet.weight_kg,
                status: 'completed',
              }
            : createDefaultSet();
          return { ...ex, sets: [...ex.sets, newSet] };
        }),
      );
    },
    [setExercises],
  );

  const removeSet = useCallback(
    (exerciseId: string, setId: string) => {
      setExercises((prev) =>
        prev.map((ex) => {
          if (ex.id !== exerciseId) return ex;
          const filtered = ex.sets.filter((s) => s.id !== setId);
          return { ...ex, sets: filtered.length === 0 ? [createDefaultSet()] : filtered };
        }),
      );
    },
    [setExercises],
  );

  // --- Autocomplete helpers ---

  const getFilteredSuggestions = useCallback(
    (query: string) => {
      if (!query.trim() || query.trim().length < 2) return [];
      const q = query.toLowerCase();
      return libraryExercises.filter((ex) => ex.name.toLowerCase().includes(q)).slice(0, 8);
    },
    [libraryExercises],
  );

  const selectSuggestion = useCallback(
    (exerciseId: string, suggestion: Exercise) => {
      updateExercise(exerciseId, {
        name: suggestion.name,
        category: (suggestion.category as ExerciseCategory) || 'push',
      });
      setActiveAutocomplete(null);
    },
    [updateExercise],
  );

  // --- Tonnage ---

  const exerciseInputs: ExerciseInput[] = useMemo(
    () =>
      exercises
        .filter((f) => f.name.trim())
        .map((f) => ({
          name: f.name,
          category: f.category,
          sets: f.sets.map((s) => ({ reps: s.reps, weight_kg: s.weight_kg, status: s.status })),
        })),
    [exercises],
  );

  const totalTonnage = useMemo(() => calculateTonnage(exerciseInputs), [exerciseInputs]);
  const perExerciseTonnage = useMemo(
    () => calculatePerExerciseTonnage(exerciseInputs),
    [exerciseInputs],
  );
  const formattedTonnage = useMemo(() => formatTonnage(totalTonnage), [totalTonnage]);

  // Map exercise names to per-exercise tonnage index
  const exerciseTonnageByName = useMemo(() => {
    const map = new Map<string, number>();
    const named = exercises.filter((f) => f.name.trim());
    named.forEach((ex, i) => {
      map.set(ex.id, perExerciseTonnage.get(i) ?? 0);
    });
    return map;
  }, [exercises, perExerciseTonnage]);

  // --- Render ---

  return (
    <div className="space-y-6">
      {exercises.map((exercise) => {
        const suggestions =
          activeAutocomplete === exercise.id ? getFilteredSuggestions(exercise.name) : [];

        return (
          <div
            key={exercise.id}
            className="rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] p-4 space-y-4"
          >
            {/* Exercise name + category + delete */}
            <div className="flex items-start gap-2 flex-wrap sm:flex-nowrap">
              <div
                className="flex-1 min-w-0 basis-full sm:basis-auto relative"
                ref={activeAutocomplete === exercise.id ? autocompleteRef : undefined}
              >
                <Input
                  value={exercise.name}
                  onChange={(e) => {
                    updateExercise(exercise.id, { name: e.target.value });
                    setActiveAutocomplete(e.target.value.trim().length >= 2 ? exercise.id : null);
                  }}
                  onFocus={() => {
                    if (exercise.name.trim().length >= 2) setActiveAutocomplete(exercise.id);
                  }}
                  placeholder="Übungsname"
                  inputSize="md"
                />
                {suggestions.length > 0 &&
                  /* prettier-ignore */
                  <div className="absolute z-20 left-0 right-0 top-full mt-1 rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] shadow-[var(--shadow-md)] max-h-48 overflow-y-auto"> {/* // ds-ok */}
                    {suggestions.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-subtle)] transition-colors duration-150 motion-reduce:transition-none"
                        onClick={() => selectSuggestion(exercise.id, s)}
                      >
                        {s.name}
                        <span className="ml-2 text-xs text-[var(--color-text-muted)]">
                          {CATEGORY_SELECT_OPTIONS.find((o) => o.value === s.category)?.label ??
                            s.category}
                        </span>
                      </button>
                    ))}
                  </div>}
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 sm:w-36 shrink-0">
                  <Select
                    options={CATEGORY_SELECT_OPTIONS}
                    value={exercise.category}
                    onChange={(val) =>
                      updateExercise(exercise.id, {
                        category: (val as ExerciseCategory) || 'push',
                      })
                    }
                    inputSize="md"
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeExercise(exercise.id)}
                  aria-label="Übung entfernen"
                  className="!p-1"
                >
                  <Trash2 className="w-4 h-4 text-[var(--color-text-muted)]" />
                </Button>
              </div>
            </div>

            {/* Per-exercise tonnage */}
            {(() => {
              const exTonnage = exerciseTonnageByName.get(exercise.id) ?? 0;
              if (exTonnage <= 0) return null;
              const fmt = formatTonnage(exTonnage);
              return (
                <div className="text-xs text-[var(--color-text-muted)] tabular-nums">
                  Tonnage: {fmt.value}
                  <span className="ml-0.5">{fmt.unit}</span>
                </div>
              );
            })()}

            {/* Sets header */}
            <div className="grid grid-cols-[auto_1fr_1fr_1fr_auto] gap-2 items-center px-1">
              <span className="text-xs text-[var(--color-text-muted)] w-6 text-center">#</span>
              <span className="text-xs text-[var(--color-text-muted)]">Wdh.</span>
              <span className="text-xs text-[var(--color-text-muted)]">kg</span>
              <span className="text-xs text-[var(--color-text-muted)]">Status</span>
              <span className="w-8" />
            </div>

            {/* Set rows */}
            {exercise.sets.map((set, setIndex) => (
              <div
                key={set.id}
                className={`grid grid-cols-[auto_1fr_1fr_1fr_auto] gap-2 items-center px-1 ${
                  set.status === 'skipped' ? 'opacity-50' : ''
                }`}
              >
                <span className="text-sm text-[var(--color-text-muted)] w-6 text-center tabular-nums">
                  {setIndex + 1}
                </span>
                <NumberInput
                  value={set.reps}
                  onChange={(val) => updateSet(exercise.id, set.id, { reps: val })}
                  min={0}
                  max={999}
                  step={1}
                  inputSize="sm"
                  decrementLabel="Reps reduzieren"
                  incrementLabel="Reps erhöhen"
                />
                <NumberInput
                  value={set.weight_kg}
                  onChange={(val) => updateSet(exercise.id, set.id, { weight_kg: val })}
                  min={0}
                  max={999}
                  step={2.5}
                  inputSize="sm"
                  decrementLabel="Gewicht reduzieren"
                  incrementLabel="Gewicht erhöhen"
                />
                <Select
                  options={STATUS_SELECT_OPTIONS}
                  value={set.status}
                  onChange={(val) =>
                    updateSet(exercise.id, set.id, {
                      status: (val as SetStatus) || 'completed',
                    })
                  }
                  inputSize="sm"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSet(exercise.id, set.id)}
                  aria-label={`Satz ${setIndex + 1} entfernen`}
                  className="!p-1"
                >
                  <Trash2 className="w-4 h-4 text-[var(--color-text-muted)]" />
                </Button>
              </div>
            ))}

            {/* Add set */}
            <div className="flex justify-center pt-1">
              <Button variant="ghost" size="sm" onClick={() => addSet(exercise.id)}>
                <Plus className="w-3.5 h-3.5 mr-1" />
                Satz hinzufügen
              </Button>
            </div>
          </div>
        );
      })}

      {/* Tonnage summary */}
      {!hideTonnageSummary && totalTonnage > 0 && (
        <div
          className="rounded-[var(--radius-component-md)] border border-[var(--color-border-subtle)] bg-[var(--color-bg-subtle)] px-4 py-2 flex items-center justify-between"
          aria-live="polite"
        >
          <span className="text-sm text-[var(--color-text-muted)]">Gesamt-Tonnage</span>
          <span className="text-lg font-semibold text-[var(--color-text-base)] tabular-nums">
            {formattedTonnage.value}
            <span className="text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
              {formattedTonnage.unit}
            </span>
          </span>
        </div>
      )}

      {/* Add exercise button */}
      <div className="flex justify-center">
        <Button variant="ghost" onClick={addExercise}>
          <Plus className="w-4 h-4 mr-2" />
          Übung hinzufügen
        </Button>
      </div>
    </div>
  );
}
