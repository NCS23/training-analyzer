/**
 * Inline-Editor für Übungen einer gespeicherten Kraftsession.
 * UI 1:1 identisch mit der Erfassungsseite (StrengthSession.tsx).
 * Wird in SessionDetail im globalen Bearbeiten-Modus angezeigt.
 * Die Eltern-Komponente ruft save() über den Ref auf.
 */
import {
  useState,
  useCallback,
  useImperativeHandle,
  forwardRef,
  useEffect,
  useRef,
  useMemo,
} from 'react';
import { Button, Card, CardBody, Input, NumberInput, Badge, useToast } from '@nordlig/components';
import { Dumbbell, Plus, Trash2, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { updateStrengthExercises, getLastExerciseSets } from '@/api/strength';
import type { ExerciseCategory, SetStatus, ExerciseInput } from '@/api/strength';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import { categoryBadgeVariant } from '@/constants/training';
import { useTonnageCalc, formatTonnage } from '@/hooks/useTonnageCalc';

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
  collapsed: boolean;
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

const CATEGORY_OPTIONS: { value: ExerciseCategory; label: string }[] = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

const CATEGORY_LABELS: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Lauf-ABC',
};

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
    collapsed: false,
    sets: ex.sets.map((s) => ({
      id: genId(),
      reps: s.reps,
      weight_kg: s.weight_kg,
      status: (s.status || 'completed') as SetStatus,
    })),
  }));
}

/** Convert ExerciseForm[] to ExerciseInput[] for tonnage calc. */
function toExerciseInputs(forms: ExerciseForm[]): ExerciseInput[] {
  return forms
    .filter((f) => f.name.trim())
    .map((f) => ({
      name: f.name,
      category: f.category,
      sets: f.sets.map((s) => ({ reps: s.reps, weight_kg: s.weight_kg, status: s.status })),
    }));
}

// --- Component ---

export const StrengthExercisesEditor = forwardRef<
  StrengthExercisesEditorRef,
  StrengthExercisesEditorProps
>(function StrengthExercisesEditor({ sessionId, exercises: initialExercises }, ref) {
  const { toast } = useToast();
  const [exercises, setExercises] = useState<ExerciseForm[]>(() => toForms(initialExercises));

  // Exercise library for suggestions
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
  }, []);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Live tonnage
  const exerciseInputs = useMemo(() => toExerciseInputs(exercises), [exercises]);
  const tonnage = useTonnageCalc(exerciseInputs);

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
              collapsed: false,
            },
          ]
        : filtered;
    });
  }, []);

  const addExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      {
        id: genId(),
        name: '',
        category: 'push' as ExerciseCategory,
        sets: [createDefaultSet()],
        collapsed: false,
      },
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

  // --- Quick-Add: Load last session's sets ---

  const loadLastSets = useCallback(
    async (exId: string, exerciseName: string) => {
      if (!exerciseName.trim()) return;
      try {
        const res = await getLastExerciseSets(exerciseName);
        if (res.found && res.exercise) {
          const loadedSets: SetForm[] = res.exercise.sets.map((s) => ({
            id: genId(),
            reps: s.reps,
            weight_kg: s.weight_kg,
            status: (s.status as SetStatus) || 'completed',
          }));
          updateExercise(exId, {
            sets: loadedSets,
            category: (res.exercise.category as ExerciseCategory) || 'push',
          });
        }
      } catch {
        // Silently fail
      }
    },
    [updateExercise],
  );

  // --- Exercise name suggestions ---

  const getFilteredSuggestions = useCallback(
    (query: string): Exercise[] => {
      if (!query.trim()) return libraryExercises.slice(0, 10);
      const lower = query.toLowerCase();
      return libraryExercises.filter((ex) => ex.name.toLowerCase().includes(lower)).slice(0, 8);
    },
    [libraryExercises],
  );

  const selectSuggestion = useCallback(
    (exId: string, exercise: Exercise) => {
      const categoryMap: Record<string, ExerciseCategory> = {
        push: 'push',
        pull: 'pull',
        legs: 'legs',
        core: 'core',
        cardio: 'cardio',
      };
      updateExercise(exId, {
        name: exercise.name,
        category: categoryMap[exercise.category] ?? 'push',
      });
      setShowSuggestions(null);
      loadLastSets(exId, exercise.name);
    },
    [updateExercise, loadLastSets],
  );

  // --- Render ---

  return (
    <div className="space-y-4">
      {exercises.map((exercise, exIndex) => (
        <Card key={exercise.id} elevation="raised" padding="spacious">
          <CardBody>
            <div className="space-y-4">
              {/* Exercise Header */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Dumbbell className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  <span className="text-xs font-medium text-[var(--color-text-muted)]">
                    Übung {exIndex + 1}
                  </span>
                  {exercise.name && (
                    <>
                      <Badge
                        variant={categoryBadgeVariant[exercise.category] ?? 'neutral'}
                        size="xs"
                      >
                        {CATEGORY_LABELS[exercise.category] ?? exercise.category}
                      </Badge>
                      {(tonnage.perExercise.get(exIndex) ?? 0) > 0 && (
                        <span className="text-xs text-[var(--color-text-muted)] tabular-nums">
                          {formatTonnage(tonnage.perExercise.get(exIndex) ?? 0).value}
                          {formatTonnage(tonnage.perExercise.get(exIndex) ?? 0).unit}
                        </span>
                      )}
                    </>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  {exercise.name && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        updateExercise(exercise.id, { collapsed: !exercise.collapsed })
                      }
                      aria-label={exercise.collapsed ? 'Aufklappen' : 'Zuklappen'}
                    >
                      {exercise.collapsed ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronUp className="w-4 h-4" />
                      )}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeExercise(exercise.id)}
                    aria-label="Übung entfernen"
                  >
                    <Trash2 className="w-4 h-4 text-[var(--color-text-error)]" />
                  </Button>
                </div>
              </div>

              {/* Exercise Name (with suggestions) */}
              {!exercise.collapsed && (
                <>
                  <div
                    className="relative"
                    ref={showSuggestions === exercise.id ? suggestionsRef : undefined}
                  >
                    <Input
                      value={exercise.name}
                      onChange={(e) => {
                        updateExercise(exercise.id, { name: e.target.value });
                        setShowSuggestions(exercise.id);
                      }}
                      onFocus={() => setShowSuggestions(exercise.id)}
                      placeholder="Übungsname (z.B. Bankdrücken)"
                      inputSize="md"
                    />
                    {showSuggestions === exercise.id && (
                      <div className="absolute z-10 mt-1 w-full rounded-[var(--radius-component-md)] bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] shadow-[var(--shadow-md)] max-h-48 overflow-y-auto">
                        {' '}
                        {/* ds-ok: uses token */}
                        {getFilteredSuggestions(exercise.name).map((ex) => (
                          <button
                            key={ex.id}
                            type="button"
                            className="w-full text-left px-3 py-2.5 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-muted)] transition-colors duration-150 motion-reduce:transition-none flex items-center justify-between"
                            onClick={() => selectSuggestion(exercise.id, ex)}
                          >
                            <span>{ex.name}</span>
                            <Badge
                              variant={categoryBadgeVariant[ex.category] ?? 'neutral'}
                              size="xs"
                            >
                              {CATEGORY_LABELS[ex.category] ?? ex.category}
                            </Badge>
                          </button>
                        ))}
                        {getFilteredSuggestions(exercise.name).length === 0 && (
                          <p className="px-3 py-2.5 text-xs text-[var(--color-text-muted)]">
                            Keine Übung gefunden. Name wird neu angelegt.
                          </p>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Category selector (only for exercises not in library) */}
                  {exercise.name && !libraryExercises.some((l) => l.name === exercise.name) && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-[var(--color-text-muted)]">Kategorie:</span>
                      {CATEGORY_OPTIONS.map((cat) => (
                        <button
                          key={cat.value}
                          type="button"
                          onClick={() => updateExercise(exercise.id, { category: cat.value })}
                          className={`px-2.5 py-1 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none ${
                            exercise.category === cat.value
                              ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-primary-1-600)] font-medium'
                              : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
                          }`}
                        >
                          {cat.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Sets */}
                  {exercise.name && (
                    <div className="space-y-2">
                      {/* Header row */}
                      <div className="grid grid-cols-[auto_1fr_1fr_auto] gap-2 items-center px-1">
                        <span className="text-xs text-[var(--color-text-muted)] w-6 text-center">
                          #
                        </span>
                        <span className="text-xs text-[var(--color-text-muted)]">Reps</span>
                        <span className="text-xs text-[var(--color-text-muted)]">Gewicht (kg)</span>
                        <span className="w-8" />
                      </div>

                      {/* Set rows */}
                      {exercise.sets.map((set, setIndex) => (
                        <div
                          key={set.id}
                          className={`grid grid-cols-[auto_1fr_1fr_auto] gap-2 items-center rounded-[var(--radius-component-md)] px-1 py-1 ${
                            set.status === 'skipped' ? 'opacity-50' : ''
                          }`}
                        >
                          <button
                            type="button"
                            onClick={() => {
                              const statusCycle: SetStatus[] = ['completed', 'reduced', 'skipped'];
                              const currentIdx = statusCycle.indexOf(set.status);
                              const nextStatus = statusCycle[(currentIdx + 1) % statusCycle.length];
                              updateSet(exercise.id, set.id, { status: nextStatus });
                            }}
                            className={`w-6 h-6 rounded-full text-xs font-medium flex items-center justify-center transition-colors duration-150 motion-reduce:transition-none ${
                              set.status === 'completed'
                                ? 'bg-[var(--color-bg-success-subtle)] text-[var(--color-text-success)]'
                                : set.status === 'reduced'
                                  ? 'bg-[var(--color-bg-warning-subtle)] text-[var(--color-text-warning)]'
                                  : 'bg-[var(--color-bg-surface)] text-[var(--color-text-disabled)]'
                            }`}
                            aria-label={`Satz ${setIndex + 1} Status: ${set.status}`}
                            title="Tippen zum Ändern: Vollständig → Reduziert → Übersprungen"
                          >
                            {setIndex + 1}
                          </button>
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
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeSet(exercise.id, set.id)}
                            aria-label={`Satz ${setIndex + 1} entfernen`}
                            className="!p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                          </Button>
                        </div>
                      ))}

                      {/* Add set + Quick-Add */}
                      <div className="flex items-center gap-2 pt-1">
                        <Button variant="ghost" size="sm" onClick={() => addSet(exercise.id)}>
                          <Plus className="w-3.5 h-3.5 mr-1" />
                          Satz
                        </Button>
                        {exercise.name.trim() && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => loadLastSets(exercise.id, exercise.name)}
                          >
                            <Copy className="w-3.5 h-3.5 mr-1" />
                            Letzte Session
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Collapsed summary */}
              {exercise.collapsed && exercise.name && (
                <p className="text-sm text-[var(--color-text-muted)]">
                  {exercise.sets.length} Sätze ·{' '}
                  {exercise.sets
                    .filter((s) => s.status !== 'skipped')
                    .reduce((sum, s) => sum + s.reps, 0)}{' '}
                  Reps ·{' '}
                  {Math.round(
                    exercise.sets
                      .filter((s) => s.status !== 'skipped')
                      .reduce((sum, s) => sum + s.reps * s.weight_kg, 0),
                  )}{' '}
                  kg Tonnage
                </p>
              )}
            </div>
          </CardBody>
        </Card>
      ))}

      {/* Add exercise button */}
      <Button variant="secondary" onClick={addExercise} className="w-full">
        <Plus className="w-4 h-4 mr-2" />
        Übung hinzufügen
      </Button>
    </div>
  );
});
