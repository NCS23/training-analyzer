/**
 * Hook for strength training upload state and handlers.
 */
import { useState, useCallback, useEffect } from 'react';
import type { NavigateFunction } from 'react-router-dom';
import type { ExerciseInput, SetType } from '@/api/strength';
import { createStrengthSession, getLastCompleteStrengthSession } from '@/api/strength';
import type { LastCompleteSession } from '@/api/strength';
import type { Exercise } from '@/api/exercises';
import { listExercises } from '@/api/exercises';
import { listSessionTemplates, getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
import { useTonnageCalc, formatTonnage } from '@/hooks/useTonnageCalc';
import { formatLocalDate } from '@/utils/weeklyPlanUtils';

const defaultExercise: ExerciseInput = {
  name: '',
  category: 'push',
  sets: [{ type: 'weight_reps', reps: 8, weight_kg: 0, status: 'completed' }],
};

interface UseStrengthUploadOptions {
  trainingType: string;
  trainingDate: Date;
  notes: string;
  rpe: number;
  csvFile: File | null;
  selectedPlannedId: number | null;
  navigate: NavigateFunction;
  setCreating: (v: boolean) => void;
  setError: (v: string | null) => void;
}

// eslint-disable-next-line max-lines-per-function -- consolidated strength upload hook
export function useStrengthUpload({
  trainingType,
  trainingDate,
  notes,
  rpe,
  csvFile,
  selectedPlannedId,
  navigate,
  setCreating,
  setError,
}: UseStrengthUploadOptions) {
  const [duration, setDuration] = useState(60);
  const [exercises, setExercises] = useState<ExerciseInput[]>([{ ...defaultExercise }]);
  const [setTypes, setSetTypes] = useState<SetType[]>(['weight_reps']);
  const [exerciseLibrary, setExerciseLibrary] = useState<Exercise[]>([]);
  const [availableTemplates, setAvailableTemplates] = useState<SessionTemplateSummary[]>([]);
  const [lastSession, setLastSession] = useState<LastCompleteSession | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);

  // Load strength data when switching to strength mode
  useEffect(() => {
    if (trainingType === 'strength') {
      listExercises()
        .then((res) => setExerciseLibrary(res.exercises))
        .catch(() => {});
      listSessionTemplates('strength')
        .then((res) => setAvailableTemplates(res.templates))
        .catch(() => {});
      getLastCompleteStrengthSession()
        .then((res) => {
          if (res.found && res.session) setLastSession(res.session);
        })
        .catch(() => {});
    }
  }, [trainingType]);

  // Exercise CRUD
  const handleExerciseChange = useCallback((idx: number, updated: ExerciseInput) => {
    setExercises((prev) => {
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  }, []);

  const handleSetTypeChange = useCallback((idx: number, newSetType: SetType) => {
    setSetTypes((prev) => {
      const next = [...prev];
      next[idx] = newSetType;
      return next;
    });
  }, []);

  const handleExerciseRemove = useCallback((idx: number) => {
    setExercises((prev) => prev.filter((_, i) => i !== idx));
    setSetTypes((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const handleAddExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      {
        ...defaultExercise,
        sets: [{ type: 'weight_reps', reps: 8, weight_kg: 0, status: 'completed' }],
      },
    ]);
    setSetTypes((prev) => [...prev, 'weight_reps']);
  }, []);

  const handleCloneLastSession = useCallback(() => {
    if (!lastSession) return;
    const hasContent = exercises.some((ex) => ex.name.trim());
    if (hasContent && !window.confirm('Aktuelle Eingabe überschreiben?')) return;
    const clonedExercises = lastSession.exercises.map((ex) => ({
      name: ex.name,
      category: ex.category,
      sets: ex.sets.map((s) => ({ ...s, status: 'completed' as const })),
    }));
    setExercises(clonedExercises);
    setSetTypes(clonedExercises.map((ex) => (ex.sets[0]?.type as SetType) || 'weight_reps'));
    if (lastSession.duration_minutes) setDuration(lastSession.duration_minutes);
  }, [lastSession, exercises]);

  const handleLoadFromPlan = useCallback(
    async (planId: number) => {
      setLoadingPlan(true);
      try {
        const plan = await getSessionTemplate(planId);
        const loaded: ExerciseInput[] = plan.exercises.map((ex) => ({
          name: ex.name,
          category: ex.category,
          sets: Array.from({ length: ex.sets }, () => ({
            type: 'weight_reps' as SetType,
            reps: ex.reps,
            weight_kg: ex.weight_kg ?? 0,
            status: 'completed' as const,
          })),
        }));
        if (loaded.length > 0) {
          setExercises(loaded);
          setSetTypes(loaded.map(() => 'weight_reps'));
        }
      } catch {
        setError('Plan konnte nicht geladen werden.');
      } finally {
        setLoadingPlan(false);
      }
    },
    [setError],
  );

  // Tonnage calculation
  const namedExercises = exercises.filter((ex) => ex.name.trim());
  const tonnage = useTonnageCalc(namedExercises);
  const tonnageDelta =
    lastSession && tonnage.total > 0 ? tonnage.total - lastSession.total_tonnage_kg : null;
  const formatted = formatTonnage(tonnage.total);

  const canSubmitStrength =
    exercises.length > 0 && exercises.every((ex) => ex.name.trim().length > 0);

  // Submit strength session
  const handleCreateStrength = useCallback(async () => {
    if (!canSubmitStrength) return;
    setCreating(true);
    setError(null);
    try {
      const result = await createStrengthSession({
        date: formatLocalDate(trainingDate),
        duration_minutes: duration,
        exercises,
        notes: notes.trim() || undefined,
        rpe,
        trainingFile: csvFile || undefined,
        plannedEntryId: selectedPlannedId ?? undefined,
      });
      if (result.success) {
        navigate(`/sessions/${result.session_id}`, { state: { uploaded: true } });
      }
    } catch (err) {
      setError('Fehler beim Speichern: ' + (err as Error).message);
    } finally {
      setCreating(false);
    }
  }, [
    canSubmitStrength,
    trainingDate,
    duration,
    exercises,
    notes,
    rpe,
    csvFile,
    selectedPlannedId,
    navigate,
    setCreating,
    setError,
  ]);

  return {
    duration,
    setDuration,
    exercises,
    setTypes,
    exerciseLibrary,
    availableTemplates,
    lastSession,
    loadingPlan,
    tonnage,
    tonnageDelta,
    formatted,
    canSubmitStrength,
    handleExerciseChange,
    handleSetTypeChange,
    handleExerciseRemove,
    handleAddExercise,
    handleCloneLastSession,
    handleLoadFromPlan,
    handleCreateStrength,
  };
}
