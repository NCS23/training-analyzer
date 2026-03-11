/**
 * Inline-Editor für Übungen einer gespeicherten Kraftsession.
 * Wird in SessionDetail im globalen Bearbeiten-Modus angezeigt.
 * Die Eltern-Komponente ruft save() über den Ref auf.
 */
import { useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Button, Input, Select, Badge, useToast } from '@nordlig/components';
import { Plus, Trash2, Check, AlertTriangle, Ban } from 'lucide-react';
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

// --- Helpers ---

const CATEGORY_OPTIONS: { value: string; label: string }[] = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

const STATUS_ICONS: Record<string, typeof Check> = {
  completed: Check,
  reduced: AlertTriangle,
  skipped: Ban,
};

const STATUS_LABELS: Record<string, string> = {
  completed: 'Fertig',
  reduced: 'Reduziert',
  skipped: 'Ausgelassen',
};

let nextId = 0;
function genId(): string {
  return `edit-${++nextId}-${Date.now()}`;
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

  const updateExercise = useCallback((exId: string, patch: Partial<ExerciseForm>) => {
    setExercises((prev) => prev.map((ex) => (ex.id === exId ? { ...ex, ...patch } : ex)));
  }, []);

  const updateSet = useCallback((exId: string, setId: string, patch: Partial<SetForm>) => {
    setExercises((prev) =>
      prev.map((ex) =>
        ex.id === exId
          ? {
              ...ex,
              sets: ex.sets.map((s) => (s.id === setId ? { ...s, ...patch } : s)),
            }
          : ex,
      ),
    );
  }, []);

  const addSet = useCallback((exId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exId) return ex;
        const lastSet = ex.sets[ex.sets.length - 1];
        return {
          ...ex,
          sets: [
            ...ex.sets,
            {
              id: genId(),
              reps: lastSet?.reps ?? 10,
              weight_kg: lastSet?.weight_kg ?? 0,
              status: 'completed' as SetStatus,
            },
          ],
        };
      }),
    );
  }, []);

  const removeSet = useCallback((exId: string, setId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exId) return ex;
        if (ex.sets.length <= 1) return ex;
        return { ...ex, sets: ex.sets.filter((s) => s.id !== setId) };
      }),
    );
  }, []);

  const addExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      {
        id: genId(),
        name: '',
        category: 'push' as ExerciseCategory,
        sets: [{ id: genId(), reps: 10, weight_kg: 0, status: 'completed' as SetStatus }],
      },
    ]);
  }, []);

  const removeExercise = useCallback((exId: string) => {
    setExercises((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((ex) => ex.id !== exId);
    });
  }, []);

  const cycleStatus = useCallback((exId: string, setId: string) => {
    const order: SetStatus[] = ['completed', 'reduced', 'skipped'];
    setExercises((prev) =>
      prev.map((ex) =>
        ex.id === exId
          ? {
              ...ex,
              sets: ex.sets.map((s) => {
                if (s.id !== setId) return s;
                const idx = order.indexOf(s.status);
                return { ...s, status: order[(idx + 1) % order.length] };
              }),
            }
          : ex,
      ),
    );
  }, []);

  return (
    <div className="space-y-4">
      {exercises.map((ex, exIdx) => (
        <div
          key={ex.id}
          className="rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] p-3 space-y-3"
        >
          {/* Übung Header */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-[var(--color-text-muted)] shrink-0">
              {exIdx + 1}.
            </span>
            <Input
              value={ex.name}
              onChange={(e) => updateExercise(ex.id, { name: e.target.value })}
              placeholder="Übungsname"
              className="flex-1"
            />
            <Select
              options={CATEGORY_OPTIONS}
              value={ex.category}
              onChange={(val) =>
                updateExercise(ex.id, {
                  category: (val as ExerciseCategory) || 'push',
                })
              }
              className="w-28 shrink-0"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeExercise(ex.id)}
              disabled={exercises.length <= 1}
              aria-label="Übung entfernen"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>

          {/* Sets */}
          <div className="space-y-1.5">
            {ex.sets.map((s, sIdx) => {
              const SIcon = STATUS_ICONS[s.status] ?? Check;
              return (
                <div key={s.id} className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-muted)] w-5 text-right shrink-0">
                    {sIdx + 1}
                  </span>
                  <Input
                    type="number"
                    min={0}
                    max={999}
                    value={s.reps}
                    onChange={(e) =>
                      updateSet(ex.id, s.id, {
                        reps: Math.max(0, parseInt(e.target.value) || 0),
                      })
                    }
                    className="w-16"
                    aria-label={`Satz ${sIdx + 1} Wiederholungen`}
                  />
                  <span className="text-xs text-[var(--color-text-muted)]">&times;</span>
                  <Input
                    type="number"
                    min={0}
                    max={999}
                    step={0.5}
                    value={s.weight_kg}
                    onChange={(e) =>
                      updateSet(ex.id, s.id, {
                        weight_kg: Math.max(0, parseFloat(e.target.value) || 0),
                      })
                    }
                    className="w-20"
                    aria-label={`Satz ${sIdx + 1} Gewicht`}
                  />
                  <span className="text-xs text-[var(--color-text-muted)]">kg</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => cycleStatus(ex.id, s.id)}
                    className="shrink-0"
                    aria-label={`Status: ${STATUS_LABELS[s.status]}`}
                  >
                    <Badge
                      variant={
                        s.status === 'completed'
                          ? 'success'
                          : s.status === 'reduced'
                            ? 'warning'
                            : 'info'
                      }
                      size="xs"
                    >
                      <SIcon className="w-3 h-3" />
                    </Badge>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSet(ex.id, s.id)}
                    disabled={ex.sets.length <= 1}
                    aria-label="Satz entfernen"
                    className="shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              );
            })}
            <Button variant="ghost" size="sm" onClick={() => addSet(ex.id)} className="mt-1">
              <Plus className="w-3.5 h-3.5 mr-1" />
              Satz
            </Button>
          </div>
        </div>
      ))}

      {/* Übung hinzufügen */}
      <Button variant="secondary" size="sm" onClick={addExercise} className="w-full">
        <Plus className="w-4 h-4 mr-1.5" />
        Übung hinzufügen
      </Button>

      {/* Tonnage-Vorschau */}
      {(() => {
        let tonnage = 0;
        for (const ex of exercises) {
          for (const s of ex.sets) {
            if (s.status !== 'skipped') tonnage += s.reps * s.weight_kg;
          }
        }
        if (tonnage <= 0) return null;
        return (
          <div className="text-xs text-[var(--color-text-muted)]">
            Tonnage:{' '}
            {tonnage >= 1000 ? `${(tonnage / 1000).toFixed(1)} t` : `${Math.round(tonnage)} kg`}
          </div>
        );
      })()}
    </div>
  );
});
