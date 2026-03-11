import { useState, useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Label,
  NumberInput,
  Slider,
  Spinner,
  Alert,
  AlertDescription,
} from '@nordlig/components';
import { DatePicker } from '@nordlig/components';
import { ClipboardList, Save, ArrowLeft, RotateCcw, TrendingUp, TrendingDown } from 'lucide-react';
import { createStrengthSession, getLastCompleteStrengthSession } from '@/api/strength';
import type {
  ExerciseCategory,
  ExerciseInput,
  LastCompleteSession,
  SetStatus,
} from '@/api/strength';
import { listSessionTemplates, getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
import { useTonnageCalc } from '@/hooks/useTonnageCalc';
import { ExerciseFormSection } from '@/components/ExerciseFormSection';
import { genId, createDefaultExercise } from '@/components/exercise-form-helpers';
import type { ExerciseForm } from '@/components/exercise-form-helpers';

// --- Constants ---

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

/** Convert ExerciseForm[] to ExerciseInput[] for tonnage calc + API. */
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

  useEffect(() => {
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
    }));
    if (cloned.length > 0) {
      setExercises(cloned);
      if (lastSession.duration_minutes) {
        setDurationMinutes(lastSession.duration_minutes);
      }
    }
  }, [lastSession, exercises]);

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
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <h2 className="text-base font-semibold text-[var(--color-text-base)] mb-4">
            Übungen ({exercises.filter((ex) => ex.name.trim()).length || exercises.length})
          </h2>
          <ExerciseFormSection
            exercises={exercises}
            setExercises={setExercises}
            hideTonnageSummary
          />
        </CardBody>
      </Card>

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
                className="w-full rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-input-bg)] px-3 py-2 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] transition-colors duration-150 motion-reduce:transition-none resize-none"
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
