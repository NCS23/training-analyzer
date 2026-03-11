/**
 * Inline-Editor für Übungen einer gespeicherten Kraftsession.
 * UI identisch mit der Erfassungsseite (StrengthSession.tsx).
 * Wird in SessionDetail im globalen Bearbeiten-Modus angezeigt.
 * Die Eltern-Komponente ruft save() über den Ref auf.
 */
import { useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Button, Input, NumberInput, Select, useToast } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import { updateStrengthExercises } from '@/api/strength';
import type { ExerciseCategory, SetStatus } from '@/api/strength';

// --- Types ---

interface SetForm {
  id: string;
  reps: number;
  weight_kg: number;
  status: SetStatus;
}

interface ExerciseForm {
  id: string;
  name: string;
  category: ExerciseCategory;
  sets: SetForm[];
}

export interface ExerciseData {
  name: string;
  category: string;
  sets: Array<{ reps: number; weight_kg: number; status: string }>;
}

export interface StrengthExercisesEditorRef {
  save: () => Promise<ExerciseData[] | null>;
}

interface StrengthExercisesEditorProps {
  sessionId: number;
  exercises: ExerciseData[];
}

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

// --- Helpers ---

let nextId = 0;
function genId(): string {
  return `edit-${++nextId}-${Date.now()}`;
}

function createDefaultSet(): SetForm {
  return { id: genId(), reps: 10, weight_kg: 0, status: 'completed' };
}

function toForms(exercises: ExerciseData[]): ExerciseForm[] {
  return exercises.map((ex) => ({
    id: genId(),
    name: ex.name,
    category: ex.category as ExerciseCategory,
    sets: ex.sets.map((s) => ({
      id: genId(),
      reps: s.reps,
      weight_kg: s.weight_kg,
      status: (s.status || 'completed') as SetStatus,
    })),
  }));
}

// --- Component ---

export const StrengthExercisesEditor = forwardRef<
  StrengthExercisesEditorRef,
  StrengthExercisesEditorProps
>(function StrengthExercisesEditor({ sessionId, exercises: initialExercises }, ref) {
  const { toast } = useToast();
  const [exercises, setExercises] = useState<ExerciseForm[]>(() => toForms(initialExercises));

  // Expose save() to parent via ref
  useImperativeHandle(ref, () => ({
    save: async () => {
      const valid = exercises.every((ex) => ex.name.trim().length > 0 && ex.sets.length > 0);
      if (!valid) {
        toast({
          title: 'Jede Übung braucht einen Namen und mindestens einen Satz.',
          variant: 'error',
        });
        return null;
      }

      const apiExercises = exercises.map((ex) => ({
        name: ex.name.trim(),
        category: ex.category,
        sets: ex.sets.map((s) => ({
          reps: s.reps,
          weight_kg: s.weight_kg,
          status: s.status,
        })),
      }));

      const result = await updateStrengthExercises(sessionId, apiExercises);
      return result.exercises;
    },
  }));

  // --- Exercise CRUD ---

  const updateExercise = useCallback((exId: string, patch: Partial<ExerciseForm>) => {
    setExercises((prev) => prev.map((ex) => (ex.id === exId ? { ...ex, ...patch } : ex)));
  }, []);

  const removeExercise = useCallback((exId: string) => {
    setExercises((prev) => {
      const filtered = prev.filter((ex) => ex.id !== exId);
      return filtered.length === 0
        ? [
            {
              id: genId(),
              name: '',
              category: 'push' as ExerciseCategory,
              sets: [createDefaultSet()],
            },
          ]
        : filtered;
    });
  }, []);

  const addExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      { id: genId(), name: '', category: 'push' as ExerciseCategory, sets: [createDefaultSet()] },
    ]);
  }, []);

  // --- Set CRUD ---

  const updateSet = useCallback((exId: string, setId: string, patch: Partial<SetForm>) => {
    setExercises((prev) =>
      prev.map((ex) =>
        ex.id === exId
          ? { ...ex, sets: ex.sets.map((s) => (s.id === setId ? { ...s, ...patch } : s)) }
          : ex,
      ),
    );
  }, []);

  const addSet = useCallback((exId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exId) return ex;
        const lastSet = ex.sets[ex.sets.length - 1];
        const newSet: SetForm = lastSet
          ? { id: genId(), reps: lastSet.reps, weight_kg: lastSet.weight_kg, status: 'completed' }
          : createDefaultSet();
        return { ...ex, sets: [...ex.sets, newSet] };
      }),
    );
  }, []);

  const removeSet = useCallback((exId: string, setId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exId) return ex;
        const filtered = ex.sets.filter((s) => s.id !== setId);
        return { ...ex, sets: filtered.length === 0 ? [createDefaultSet()] : filtered };
      }),
    );
  }, []);

  // --- Render ---

  return (
    <div className="space-y-6">
      {exercises.map((exercise) => (
        <div
          key={exercise.id}
          className="rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] p-4 space-y-4"
        >
          {/* Exercise name + category + delete */}
          <div className="flex items-start gap-2 flex-wrap sm:flex-nowrap">
            <div className="flex-1 min-w-0 basis-full sm:basis-auto">
              <Input
                value={exercise.name}
                onChange={(e) => updateExercise(exercise.id, { name: e.target.value })}
                placeholder="Übungsname"
                inputSize="md"
              />
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
              >
                <Trash2 className="w-4 h-4 text-[var(--color-text-muted)]" />
              </Button>
            </div>
          </div>

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
      ))}

      {/* Add exercise button */}
      <div className="flex justify-center">
        <Button variant="ghost" onClick={addExercise}>
          <Plus className="w-4 h-4 mr-2" />
          Übung hinzufügen
        </Button>
      </div>
    </div>
  );
});
