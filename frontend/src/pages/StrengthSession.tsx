import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  NumberInput,
  Label,
  Slider,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
} from '@nordlig/components';
import { DatePicker } from '@nordlig/components';
import {
  ClipboardList,
  Dumbbell,
  Plus,
  Trash2,
  Copy,
  ChevronDown,
  ChevronUp,
  Save,
  ArrowLeft,
  RotateCcw,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { createStrengthSession, getLastCompleteStrengthSession } from '@/api/strength';
import type {
  ExerciseCategory,
  ExerciseInput,
  LastCompleteSession,
  SetStatus,
} from '@/api/strength';
import { categoryBadgeVariant } from '@/constants/training';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import { getLastExerciseSets } from '@/api/strength';
import { listSessionTemplates, getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
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

const RPE_LABELS: Record<number, string> = {
  1: 'Sehr leicht',
  2: 'Leicht',
  3: 'Leicht-Mittel',
  4: 'Mittel',
  5: 'Mittel',
  6: 'Mittel-Schwer',
  7: 'Schwer',
  8: 'Schwer',
  9: 'Sehr schwer',
  10: 'Maximum',
};

let nextId = 0;
function genId(): string {
  return `s-${++nextId}-${Date.now()}`;
}

function createDefaultSet(): SetForm {
  return { id: genId(), reps: 10, weight_kg: 0, status: 'completed' };
}

function createDefaultExercise(): ExerciseForm {
  return {
    id: genId(),
    name: '',
    category: 'push',
    sets: [createDefaultSet()],
    collapsed: false,
  };
}

/** Convert ExerciseForm[] (with id, collapsed) to ExerciseInput[] for tonnage calc + API. */
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

export function StrengthSessionPage() {
  const navigate = useNavigate();

  // Form state
  const [trainingDate, setTrainingDate] = useState<Date>(new Date());
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [exercises, setExercises] = useState<ExerciseForm[]>([createDefaultExercise()]);
  const [rpe, setRpe] = useState<number>(5);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Session templates
  const [availableTemplates, setAvailableTemplates] = useState<SessionTemplateSummary[]>([]);
  const [loadingPlan, setLoadingPlan] = useState(false);

  // Last session (for clone + tonnage delta)
  const [lastSession, setLastSession] = useState<LastCompleteSession | null>(null);

  // Exercise library for suggestions
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
    listSessionTemplates('strength')
      .then((res) => setAvailableTemplates(res.templates))
      .catch(() => {});
    getLastCompleteStrengthSession()
      .then((res) => {
        if (res.found && res.session) setLastSession(res.session);
      })
      .catch(() => {});
  }, []);

  // Live tonnage calculation
  const exerciseInputs = useMemo(() => toExerciseInputs(exercises), [exercises]);
  const tonnage = useTonnageCalc(exerciseInputs);
  const tonnageDelta =
    lastSession && tonnage.total > 0 ? tonnage.total - lastSession.total_tonnage_kg : null;

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

  // --- Exercise CRUD ---

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

  // --- Set CRUD ---

  const updateSet = useCallback((exerciseId: string, setId: string, updates: Partial<SetForm>) => {
    setExercises((prev) =>
      prev.map((ex) =>
        ex.id === exerciseId
          ? {
              ...ex,
              sets: ex.sets.map((s) => (s.id === setId ? { ...s, ...updates } : s)),
            }
          : ex,
      ),
    );
  }, []);

  const addSet = useCallback((exerciseId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exerciseId) return ex;
        // Clone last set's values for convenience
        const lastSet = ex.sets[ex.sets.length - 1];
        const newSet: SetForm = lastSet
          ? { id: genId(), reps: lastSet.reps, weight_kg: lastSet.weight_kg, status: 'completed' }
          : createDefaultSet();
        return { ...ex, sets: [...ex.sets, newSet] };
      }),
    );
  }, []);

  const removeSet = useCallback((exerciseId: string, setId: string) => {
    setExercises((prev) =>
      prev.map((ex) => {
        if (ex.id !== exerciseId) return ex;
        const filtered = ex.sets.filter((s) => s.id !== setId);
        return { ...ex, sets: filtered.length === 0 ? [createDefaultSet()] : filtered };
      }),
    );
  }, []);

  // --- Quick-Add: Load last session's sets ---

  const loadLastSets = useCallback(
    async (exerciseId: string, exerciseName: string) => {
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
          updateExercise(exerciseId, {
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

  // --- Load from plan ---

  const loadFromPlan = useCallback(async (planId: number) => {
    setLoadingPlan(true);
    try {
      const plan = await getSessionTemplate(planId);
      const loadedExercises: ExerciseForm[] = plan.exercises.map((ex) => ({
        id: genId(),
        name: ex.name,
        category: ex.category as ExerciseCategory,
        sets: Array.from({ length: ex.sets }, () => ({
          id: genId(),
          reps: ex.reps,
          weight_kg: ex.weight_kg ?? 0,
          status: 'completed' as SetStatus,
        })),
        collapsed: false,
      }));
      if (loadedExercises.length > 0) {
        setExercises(loadedExercises);
      }
    } catch {
      setError('Plan konnte nicht geladen werden.');
    } finally {
      setLoadingPlan(false);
    }
  }, []);

  // --- Clone last session ---

  const handleCloneLastSession = useCallback(() => {
    if (!lastSession) return;
    const hasContent = exercises.some((ex) => ex.name.trim());
    if (hasContent && !window.confirm('Aktuelle Eingabe überschreiben?')) return;

    const cloned: ExerciseForm[] = lastSession.exercises.map((ex) => ({
      id: genId(),
      name: ex.name,
      category: ex.category as ExerciseCategory,
      sets: ex.sets.map((s) => ({
        id: genId(),
        reps: s.reps,
        weight_kg: s.weight_kg,
        status: 'completed' as SetStatus,
      })),
      collapsed: false,
    }));
    if (cloned.length > 0) {
      setExercises(cloned);
      if (lastSession.duration_minutes) {
        setDurationMinutes(lastSession.duration_minutes);
      }
    }
  }, [lastSession, exercises]);

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
    (exerciseId: string, exercise: Exercise) => {
      const categoryMap: Record<string, ExerciseCategory> = {
        push: 'push',
        pull: 'pull',
        legs: 'legs',
        core: 'core',
        cardio: 'cardio',
      };
      updateExercise(exerciseId, {
        name: exercise.name,
        category: categoryMap[exercise.category] ?? 'push',
      });
      setShowSuggestions(null);
      // Auto-load last sets
      loadLastSets(exerciseId, exercise.name);
    },
    [updateExercise, loadLastSets],
  );

  // --- Submit ---

  const handleSubmit = useCallback(async () => {
    // Validate
    const validExercises = exercises.filter((ex) => ex.name.trim());
    if (validExercises.length === 0) {
      setError('Mindestens eine Übung mit Namen erforderlich.');
      return;
    }
    for (const ex of validExercises) {
      const validSets = ex.sets.filter((s) => s.reps > 0);
      if (validSets.length === 0) {
        setError(`"${ex.name}" braucht mindestens einen Satz mit Wiederholungen.`);
        return;
      }
    }

    setSubmitting(true);
    setError(null);

    try {
      const result = await createStrengthSession({
        date: trainingDate.toISOString().split('T')[0],
        duration_minutes: durationMinutes,
        exercises: validExercises.map((ex) => ({
          name: ex.name.trim(),
          category: ex.category,
          sets: ex.sets
            .filter((s) => s.reps > 0)
            .map((s) => ({
              reps: s.reps,
              weight_kg: s.weight_kg,
              status: s.status,
            })),
        })),
        notes: notes.trim() || undefined,
        rpe,
      });

      navigate(`/sessions/${result.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern.');
    } finally {
      setSubmitting(false);
    }
  }, [exercises, trainingDate, durationMinutes, notes, rpe, navigate]);

  // --- Render ---

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="pb-2">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)} aria-label="Zurück">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
              Krafttraining erfassen
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Übungen, Sätze und Gewichte eintragen.
            </p>
          </div>
        </div>
      </header>

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Meta: Date + Duration */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label
                htmlFor="training-date"
                className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
              >
                Datum
              </Label>
              <DatePicker
                value={trainingDate}
                onChange={(d) => d && setTrainingDate(d)}
                maxDate={new Date()}
                inputSize="md"
              />
            </div>
            <div>
              <Label
                htmlFor="duration"
                className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
              >
                Dauer (Minuten)
              </Label>
              <NumberInput
                value={durationMinutes}
                onChange={setDurationMinutes}
                min={1}
                max={600}
                step={5}
                inputSize="md"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Load from plan */}
      {availableTemplates.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="flex items-center gap-3">
              <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
              <span className="text-xs font-medium text-[var(--color-text-muted)]">
                Aus Plan laden:
              </span>
              <div className="flex items-center gap-2 flex-wrap flex-1">
                {availableTemplates.map((plan) => (
                  <Button
                    key={plan.id}
                    variant="secondary"
                    size="sm"
                    onClick={() => loadFromPlan(plan.id)}
                    disabled={loadingPlan}
                  >
                    {plan.name}
                  </Button>
                ))}
              </div>
              {loadingPlan && <Spinner size="sm" />}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Clone last session */}
      {lastSession && (
        <Button variant="secondary" size="sm" onClick={handleCloneLastSession} className="w-full">
          <RotateCcw className="w-4 h-4 mr-2" />
          Letztes Training übernehmen ({lastSession.date})
        </Button>
      )}

      {/* Exercises */}
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

                    {/* Category selector */}
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
                          <span className="text-xs text-[var(--color-text-muted)]">
                            Gewicht (kg)
                          </span>
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
                                const statusCycle: SetStatus[] = [
                                  'completed',
                                  'reduced',
                                  'skipped',
                                ];
                                const currentIdx = statusCycle.indexOf(set.status);
                                const nextStatus =
                                  statusCycle[(currentIdx + 1) % statusCycle.length];
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

      {/* RPE + Notes */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="space-y-5">
            {/* RPE Slider */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-xs font-medium text-[var(--color-text-muted)]">
                  Belastung (RPE)
                </Label>
                <span className="text-sm font-semibold text-[var(--color-text-base)]">
                  {rpe} — {RPE_LABELS[rpe]}
                </span>
              </div>
              <Slider
                value={[rpe]}
                onValueChange={([val]) => setRpe(val)}
                min={1}
                max={10}
                step={1}
              />
            </div>

            {/* Notes */}
            <div>
              <Label
                htmlFor="notes"
                className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
              >
                Notizen (optional)
              </Label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Wie lief das Training?"
                rows={3}
                className="w-full rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] px-3 py-2 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] transition-colors duration-150 motion-reduce:transition-none resize-none"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Sticky tonnage bar + submit */}
      <div className="sticky bottom-4 z-10 space-y-2">
        {tonnage.total > 0 && (
          <div
            className="bg-[var(--color-bg-base)]/95 backdrop-blur-sm rounded-[var(--radius-component-md)] border border-[var(--color-border-subtle)] px-4 py-2 flex items-center justify-between"
            aria-live="polite"
          >
            <span className="text-sm text-[var(--color-text-muted)]">Gesamt-Tonnage</span>
            <div className="flex items-center gap-2">
              {tonnageDelta !== null && tonnageDelta !== 0 && (
                <span
                  className={`text-xs tabular-nums flex items-center gap-0.5 ${
                    tonnageDelta > 0
                      ? 'text-[var(--color-text-success)]'
                      : 'text-[var(--color-text-error)]'
                  }`}
                >
                  {tonnageDelta > 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {tonnageDelta > 0 ? '+' : ''}
                  {Math.round(tonnageDelta)} kg
                </span>
              )}
              <span className="text-lg font-semibold text-[var(--color-text-base)] tabular-nums">
                {tonnage.formatted.value}
                <span className="text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
                  {tonnage.formatted.unit}
                </span>
              </span>
            </div>
          </div>
        )}
        <Button
          variant="primary"
          onClick={handleSubmit}
          disabled={submitting || exercises.every((ex) => !ex.name.trim())}
          className="w-full"
          size="lg"
        >
          {submitting ? <Spinner size="sm" className="mr-2" /> : <Save className="w-4 h-4 mr-2" />}
          {submitting ? 'Speichern...' : 'Training speichern'}
        </Button>
      </div>
    </div>
  );
}
