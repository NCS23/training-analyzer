/**
 * Compact inline exercise editor for strength sessions.
 * Used in PhaseWeeklyTemplateEditor and DayCard (weekly plan).
 * Mirrors the exercise editing UI from SessionTemplateEditor but in a
 * compact card layout (analogous to RunDetailsEditor for running segments).
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { Input, Select, Button, Label, NumberInput, Badge } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import type { TemplateExercise } from '@/api/session-templates';
import type { ExerciseCategory } from '@/api/session-templates';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import { categoryBadgeVariant } from '@/constants/training';
import {
  type ExerciseForm,
  CATEGORY_OPTIONS,
  CATEGORY_LABELS,
  EXERCISE_TYPE_OPTIONS,
  createDefaultExercise,
  exerciseFormToApi,
  apiExerciseToForm,
} from '@/utils/exercise-helpers';

// --- Hook: exercise library ---

function useExerciseLibrary() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  useEffect(() => {
    let cancelled = false;
    listExercises()
      .then((res) => {
        if (!cancelled) setExercises(res.exercises);
      })
      .catch(() => {
        /* optional enrichment */
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return exercises;
}

// --- Sub-Components ---

interface ExerciseRowProps {
  exercise: ExerciseForm;
  libraryExercises: Exercise[];
  showSuggestions: boolean;
  onShowSuggestions: (show: boolean) => void;
  suggestionsRef: React.RefObject<HTMLDivElement | null>;
  onUpdate: (updates: Partial<ExerciseForm>) => void;
  onRemove: () => void;
}

function ExerciseRow({
  exercise,
  libraryExercises,
  showSuggestions,
  onShowSuggestions,
  suggestionsRef,
  onUpdate,
  onRemove,
}: ExerciseRowProps) {
  const getFilteredSuggestions = (query: string): Exercise[] => {
    if (!query.trim()) return libraryExercises.slice(0, 10);
    const lower = query.toLowerCase();
    return libraryExercises.filter((ex) => ex.name.toLowerCase().includes(lower)).slice(0, 8);
  };

  const selectSuggestion = (ex: Exercise) => {
    const categoryMap: Record<string, ExerciseCategory> = {
      push: 'push',
      pull: 'pull',
      legs: 'legs',
      core: 'core',
      cardio: 'cardio',
    };
    onUpdate({ name: ex.name, category: categoryMap[ex.category] ?? 'push' });
    onShowSuggestions(false);
  };

  return (
    <div className="rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] border-l-2 border-l-[var(--color-border-primary)] bg-[var(--color-bg-surface)] p-3 space-y-2">
      {/* Row 1: Name with suggestions */}
      <div className="relative" ref={showSuggestions ? suggestionsRef as React.RefObject<HTMLDivElement> : undefined}>
        <Label className="text-[10px] mb-0.5">Übung</Label>
        <Input
          value={exercise.name}
          onChange={(e) => {
            onUpdate({ name: e.target.value });
            onShowSuggestions(true);
          }}
          onFocus={() => onShowSuggestions(true)}
          placeholder="Übungsname"
          inputSize="sm"
        />
        {showSuggestions && (
          <div className="absolute z-10 mt-1 w-full rounded-[var(--radius-component-md)] bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] shadow-[var(--shadow-md)] max-h-48 overflow-y-auto">
            {getFilteredSuggestions(exercise.name).map((ex) => (
              <button
                key={ex.id}
                type="button"
                className="w-full text-left px-3 py-2.5 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-muted)] transition-colors duration-150 motion-reduce:transition-none flex items-center justify-between"
                onClick={() => selectSuggestion(ex)}
              >
                <span>{ex.name}</span>
                <Badge variant={categoryBadgeVariant[ex.category] ?? 'neutral'} size="xs">
                  {CATEGORY_LABELS[ex.category] ?? ex.category}
                </Badge>
              </button>
            ))}
            {getFilteredSuggestions(exercise.name).length === 0 && (
              <p className="px-3 py-2.5 text-xs text-[var(--color-text-muted)]">
                Keine Übung gefunden.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Row 2: Category + Type (only show when name is set) */}
      {exercise.name && (
        <div className="flex items-end gap-1.5">
          <div className="flex-1 min-w-0">
            <Label className="text-[10px] mb-0.5">Kategorie</Label>
            <Select
              options={CATEGORY_OPTIONS}
              value={exercise.category}
              onChange={(val) => {
                if (val) onUpdate({ category: val as ExerciseCategory });
              }}
              inputSize="sm"
            />
          </div>
          <div className="flex-1 min-w-0">
            <Label className="text-[10px] mb-0.5">Typ</Label>
            <Select
              options={EXERCISE_TYPE_OPTIONS}
              value={exercise.exercise_type}
              onChange={(val) => {
                if (val) onUpdate({ exercise_type: val as ExerciseForm['exercise_type'] });
              }}
              inputSize="sm"
            />
          </div>
        </div>
      )}

      {/* Row 3: Sets / Reps / Weight */}
      {exercise.name && (
        <div className="grid grid-cols-3 gap-1.5">
          <div>
            <Label className="text-[10px] mb-0.5">Sätze</Label>
            <NumberInput
              value={exercise.sets}
              onChange={(val) => onUpdate({ sets: val })}
              min={1}
              max={20}
              step={1}
              inputSize="sm"
              decrementLabel="Sätze reduzieren"
              incrementLabel="Sätze erhöhen"
            />
          </div>
          <div>
            <Label className="text-[10px] mb-0.5">Reps</Label>
            <NumberInput
              value={exercise.reps}
              onChange={(val) => onUpdate({ reps: val })}
              min={1}
              max={100}
              step={1}
              inputSize="sm"
              decrementLabel="Wiederholungen reduzieren"
              incrementLabel="Wiederholungen erhöhen"
            />
          </div>
          <div>
            <Label className="text-[10px] mb-0.5">Gewicht (kg)</Label>
            <NumberInput
              value={exercise.weight_kg}
              onChange={(val) => onUpdate({ weight_kg: val })}
              min={0}
              max={999}
              step={0.5}
              inputSize="sm"
              decrementLabel="Gewicht reduzieren"
              incrementLabel="Gewicht erhöhen"
            />
          </div>
        </div>
      )}

      {/* Row 4: Notes + Delete */}
      {exercise.name && (
        <div className="flex items-end gap-1.5">
          <div className="flex-1 min-w-0">
            <Label className="text-[10px] mb-0.5">Notiz</Label>
            <Input
              value={exercise.notes}
              onChange={(e) => onUpdate({ notes: e.target.value })}
              placeholder="Optional"
              inputSize="sm"
            />
          </div>
          <Button
            variant="destructive-outline"
            size="sm"
            onClick={onRemove}
            aria-label="Übung entfernen"
            className="shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}

      {/* Delete only (when name is not set) */}
      {!exercise.name && (
        <div className="flex justify-end">
          <Button
            variant="destructive-outline"
            size="sm"
            onClick={onRemove}
            aria-label="Übung entfernen"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}

// --- Main Component ---

interface StrengthExerciseEditorProps {
  exercises: TemplateExercise[] | null;
  onChange: (exercises: TemplateExercise[] | null) => void;
}

export function StrengthExerciseEditor({ exercises, onChange }: StrengthExerciseEditorProps) {
  // Internal form state with stable IDs
  const [forms, setForms] = useState<ExerciseForm[]>(() =>
    exercises && exercises.length > 0 ? exercises.map(apiExerciseToForm) : [],
  );

  // Sync forms when exercises prop changes externally (e.g. template picker)
  const prevExercisesRef = useRef(exercises);
  useEffect(() => {
    // Compare by JSON — only resync when the actual data changed (not identity)
    const prevJson = JSON.stringify(prevExercisesRef.current ?? []);
    const nextJson = JSON.stringify(exercises ?? []);
    if (prevJson !== nextJson) {
      prevExercisesRef.current = exercises;
      setForms(exercises && exercises.length > 0 ? exercises.map(apiExerciseToForm) : []);
    }
  }, [exercises]);

  const [activeSuggestion, setActiveSuggestion] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const libraryExercises = useExerciseLibrary();

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setActiveSuggestion(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Sync internal state → parent on every change
  const emitChange = useCallback(
    (updated: ExerciseForm[]) => {
      const valid = updated.filter((ex) => ex.name.trim());
      onChange(valid.length > 0 ? valid.map(exerciseFormToApi) : null);
    },
    [onChange],
  );

  const updateExercise = useCallback(
    (exerciseId: string, updates: Partial<ExerciseForm>) => {
      setForms((prev) => {
        const next = prev.map((ex) => (ex.id === exerciseId ? { ...ex, ...updates } : ex));
        emitChange(next);
        return next;
      });
    },
    [emitChange],
  );

  const removeExercise = useCallback(
    (exerciseId: string) => {
      setForms((prev) => {
        const filtered = prev.filter((ex) => ex.id !== exerciseId);
        emitChange(filtered);
        return filtered;
      });
    },
    [emitChange],
  );

  const addExercise = useCallback(() => {
    setForms((prev) => [...prev, createDefaultExercise()]);
  }, []);

  return (
    <div className="space-y-2">
      {forms.map((exercise) => (
        <ExerciseRow
          key={exercise.id}
          exercise={exercise}
          libraryExercises={libraryExercises}
          showSuggestions={activeSuggestion === exercise.id}
          onShowSuggestions={(show) => setActiveSuggestion(show ? exercise.id : null)}
          suggestionsRef={suggestionsRef}
          onUpdate={(updates) => updateExercise(exercise.id, updates)}
          onRemove={() => removeExercise(exercise.id)}
        />
      ))}
      <Button variant="ghost" size="sm" className="w-full" onClick={addExercise}>
        <Plus className="w-4 h-4 mr-1" />
        Übung hinzufügen
      </Button>
    </div>
  );
}
