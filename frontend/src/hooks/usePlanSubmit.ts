/**
 * Hook for training plan save and delete operations.
 */
import { useState, useCallback } from 'react';
import type { NavigateFunction } from 'react-router-dom';
import type { ToastVariant } from '@nordlig/components';
import {
  createTrainingPlan,
  getTrainingPlan,
  updateTrainingPlan,
  deleteTrainingPlan,
  addPhase,
  updatePhase,
  deletePhase,
} from '@/api/training-plans';
import type { PlanStatus } from '@/api/training-plans';
import { type PhaseForm, phaseFormToParams } from '@/hooks/usePlanForm';

interface UsePlanSubmitOptions {
  planId: string | undefined;
  isEdit: boolean;
  name: string;
  description: string;
  startDate: Date | undefined;
  endDate: Date | undefined;
  targetEventDate: Date | undefined;
  status: PlanStatus;
  goalId: number | undefined;
  restDays: number[];
  phases: PhaseForm[];
  navigate: NavigateFunction;
  toast: (data: { title: string; description?: string; variant?: ToastVariant }) => void;
}

// eslint-disable-next-line max-lines-per-function -- consolidated plan save/delete hook
export function usePlanSubmit(opts: UsePlanSubmitOptions) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteWeeklyPlans, setDeleteWeeklyPlans] = useState(false);

  // eslint-disable-next-line complexity -- phase sync logic
  const handleSave = useCallback(async () => {
    const { name, startDate, endDate, planId, isEdit, phases, navigate, toast } = opts;
    if (!name.trim()) {
      setError('Bitte einen Namen eingeben');
      return;
    }
    if (!startDate || !endDate) {
      setError('Bitte Start- und Enddatum angeben');
      return;
    }
    if (endDate <= startDate) {
      setError('Enddatum muss nach Startdatum liegen');
      return;
    }

    setSaving(true);
    setError(null);

    const formatDate = (d: Date) => d.toISOString().split('T')[0];

    try {
      if (isEdit) {
        const updatedPlan = await updateTrainingPlan(parseInt(planId!, 10), {
          name: name.trim(),
          description: opts.description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: opts.targetEventDate ? formatDate(opts.targetEventDate) : undefined,
          weekly_structure: opts.restDays.length > 0 ? { rest_days: opts.restDays } : undefined,
          status: opts.status,
          goal_id: opts.goalId,
        });

        // Sync phases: update existing, add new, delete removed
        const plan = await getTrainingPlan(parseInt(planId!, 10));
        const existingPhaseIds = new Set(plan.phases.map((p) => p.id));
        const currentPhaseIds = new Set(phases.filter((p) => p.id).map((p) => p.id!));

        for (const ep of plan.phases) {
          if (!currentPhaseIds.has(ep.id)) {
            await deletePhase(parseInt(planId!, 10), ep.id);
          }
        }

        let totalRegenerated = 0;
        let totalSkippedEdited = 0;
        for (const phase of phases) {
          const phaseData = phaseFormToParams(phase);
          if (phase.id && existingPhaseIds.has(phase.id)) {
            const result = await updatePhase(parseInt(planId!, 10), phase.id, phaseData);
            // eslint-disable-next-line max-depth
            if (result.auto_regeneration) {
              totalRegenerated += result.auto_regeneration.weeks_regenerated;
              totalSkippedEdited += result.auto_regeneration.weeks_skipped_edited;
            }
          } else {
            await addPhase(parseInt(planId!, 10), phaseData);
          }
        }

        toast({ title: 'Trainingsplan aktualisiert', variant: 'success' });

        if (updatedPlan.auto_generation_result) {
          toast({
            title: `${updatedPlan.auto_generation_result.weeks_generated} Wochenpläne automatisch erstellt`,
            variant: 'success',
          });
        }

        if (totalRegenerated > 0) {
          const editedNote =
            totalSkippedEdited > 0 ? ` (${totalSkippedEdited} bearbeitete beibehalten)` : '';
          toast({
            title: `${totalRegenerated} Wochenpläne aktualisiert${editedNote}`,
            variant: 'success',
          });
        }
      } else {
        await createTrainingPlan({
          name: name.trim(),
          description: opts.description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: opts.targetEventDate ? formatDate(opts.targetEventDate) : undefined,
          weekly_structure: opts.restDays.length > 0 ? { rest_days: opts.restDays } : undefined,
          status: opts.status,
          goal_id: opts.goalId,
          phases: phases.map(phaseFormToParams),
        });
        toast({ title: 'Trainingsplan erstellt', variant: 'success' });
      }
      navigate('/plan/programs');
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  }, [opts]);

  const handleDelete = useCallback(async () => {
    if (!opts.planId) return;
    setDeleting(true);
    try {
      await deleteTrainingPlan(parseInt(opts.planId, 10), deleteWeeklyPlans);
      opts.toast({ title: 'Trainingsplan gelöscht', variant: 'success' });
      opts.navigate('/plan/programs');
    } catch {
      opts.toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
      setDeleteWeeklyPlans(false);
    }
  }, [opts, deleteWeeklyPlans]);

  return {
    saving,
    error,
    setError,
    showDeleteDialog,
    setShowDeleteDialog,
    deleting,
    deleteWeeklyPlans,
    setDeleteWeeklyPlans,
    handleSave,
    handleDelete,
  };
}
