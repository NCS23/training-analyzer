/**
 * Hook for training plan form state, loading, and phase management.
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useToast } from '@nordlig/components';
import { getTrainingPlan } from '@/api/training-plans';
import type {
  PlanStatus,
  PhaseType,
  TrainingPlan,
  TrainingPhaseCreateParams,
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplates,
} from '@/api/training-plans';
import { listGoals } from '@/api/goals';
import type { RaceGoal } from '@/api/goals';
import { PHASE_FOCUS_DEFAULTS, normalizeFocusKey } from '@/constants/taxonomy';

export interface PhaseForm {
  id?: number;
  name: string;
  phase_type: PhaseType;
  start_week: number;
  end_week: number;
  notes: string;
  focus_primary: string[];
  focus_secondary: string[];
  weekly_template: PhaseWeeklyTemplate | null;
  weekly_templates: PhaseWeeklyTemplates | null;
}

export function phaseFormToParams(phase: PhaseForm): TrainingPhaseCreateParams {
  const focus =
    phase.focus_primary.length > 0 || phase.focus_secondary.length > 0
      ? {
          primary: phase.focus_primary,
          secondary: phase.focus_secondary.length > 0 ? phase.focus_secondary : undefined,
        }
      : undefined;
  return {
    name: phase.name,
    phase_type: phase.phase_type,
    start_week: phase.start_week,
    end_week: phase.end_week,
    focus,
    notes: phase.notes || undefined,
    weekly_template: phase.weekly_template ?? undefined,
    weekly_templates: phase.weekly_templates ?? undefined,
  };
}

// eslint-disable-next-line max-lines-per-function -- consolidated plan form hook
export function usePlanForm() {
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const isEdit = !!planId;
  const [editMode, setEditMode] = useState(() => searchParams.get('edit') === 'true');
  const isEditing = !isEdit || editMode;
  const [rawPlan, setRawPlan] = useState<TrainingPlan | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [targetEventDate, setTargetEventDate] = useState<Date | undefined>(undefined);
  const [status, setStatus] = useState<PlanStatus>('draft');
  const [goalId, setGoalId] = useState<number | undefined>(undefined);
  const [restDays, setRestDays] = useState<number[]>([]);
  const [phases, setPhases] = useState<PhaseForm[]>([]);

  // UI state
  const [loading, setLoading] = useState(isEdit);
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [weeklyPlanWeekCount, setWeeklyPlanWeekCount] = useState(0);

  // Load goals for dropdown
  useEffect(() => {
    listGoals()
      .then((res) => setGoals(res.goals))
      .catch(() => {});
  }, []);

  // Pre-fill goalId from URL param
  useEffect(() => {
    const gid = searchParams.get('goalId');
    if (gid && !isEdit) {
      setGoalId(parseInt(gid, 10));
    }
  }, [searchParams, isEdit]);

  // Load existing plan
  const loadPlan = useCallback(async () => {
    if (!planId) return;
    try {
      const plan = await getTrainingPlan(parseInt(planId, 10));
      setRawPlan(plan);
      setName(plan.name);
      setDescription(plan.description ?? '');
      setStartDate(new Date(plan.start_date));
      setEndDate(new Date(plan.end_date));
      if (plan.target_event_date) setTargetEventDate(new Date(plan.target_event_date));
      setStatus(plan.status);
      if (plan.goal_id) setGoalId(plan.goal_id);
      setRestDays(plan.weekly_structure?.rest_days ?? []);
      setWeeklyPlanWeekCount(plan.weekly_plan_week_count ?? 0);
      setPhases(
        plan.phases.map((p) => ({
          id: p.id,
          name: p.name,
          phase_type: p.phase_type,
          start_week: p.start_week,
          end_week: p.end_week,
          notes: p.notes ?? '',
          focus_primary: (p.focus?.primary ?? []).map(normalizeFocusKey),
          focus_secondary: (p.focus?.secondary ?? []).map(normalizeFocusKey),
          weekly_template: p.weekly_template ?? null,
          weekly_templates: p.weekly_templates ?? null,
        })),
      );
    } catch {
      toast({ title: 'Plan konnte nicht geladen werden', variant: 'error' });
      navigate('/plan/programs');
    } finally {
      setLoading(false);
    }
  }, [planId, toast, navigate]);

  useEffect(() => {
    if (isEdit) loadPlan();
  }, [isEdit, loadPlan]);

  // Phase helpers
  const addNewPhase = useCallback(() => {
    setPhases((prev) => {
      const lastEnd = prev.length > 0 ? prev[prev.length - 1].end_week : 0;
      const defaults = PHASE_FOCUS_DEFAULTS['base'];
      return [
        ...prev,
        {
          name: `Phase ${prev.length + 1}`,
          phase_type: 'base' as PhaseType,
          start_week: lastEnd + 1,
          end_week: lastEnd + 4,
          notes: '',
          focus_primary: [...defaults.primary],
          focus_secondary: [...defaults.secondary],
          weekly_template: null,
          weekly_templates: null,
        },
      ];
    });
  }, []);

  const updatePhaseForm = useCallback((idx: number, updates: Partial<PhaseForm>) => {
    setPhases((prev) => prev.map((p, i) => (i === idx ? { ...p, ...updates } : p)));
  }, []);

  const removePhase = useCallback((idx: number) => {
    setPhases((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  return {
    navigate,
    planId,
    toast,
    isEdit,
    editMode,
    setEditMode,
    isEditing,
    rawPlan,
    name,
    setName,
    description,
    setDescription,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    targetEventDate,
    setTargetEventDate,
    status,
    setStatus,
    goalId,
    setGoalId,
    restDays,
    phases,
    loading,
    goals,
    weeklyPlanWeekCount,
    loadPlan,
    addNewPhase,
    updatePhaseForm,
    removePhase,
  };
}
