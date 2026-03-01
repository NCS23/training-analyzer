import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  Label,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  useToast,
  Breadcrumbs,
  BreadcrumbItem,
  Select,
  DatePicker,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from '@nordlig/components';
import { Save, ArrowLeft, ChevronRight, Plus, Trash2, CalendarPlus } from 'lucide-react';
import {
  createTrainingPlan,
  getTrainingPlan,
  updateTrainingPlan,
  deleteTrainingPlan,
  addPhase,
  updatePhase,
  deletePhase,
  generateWeeklyPlans,
} from '@/api/training-plans';
import type {
  PlanStatus,
  PhaseType,
  TrainingPhaseCreateParams,
  PhaseWeeklyTemplate,
} from '@/api/training-plans';
import { listGoals } from '@/api/goals';
import type { RaceGoal } from '@/api/goals';
import { PhaseWeeklyTemplateEditor } from '@/components/PhaseWeeklyTemplateEditor';

const PHASE_TYPES: { value: PhaseType; label: string }[] = [
  { value: 'base', label: 'Grundlage' },
  { value: 'build', label: 'Aufbau' },
  { value: 'peak', label: 'Wettkampf' },
  { value: 'taper', label: 'Tapering' },
  { value: 'transition', label: 'Übergang' },
];

const PHASE_COLORS: Record<PhaseType, 'neutral' | 'info' | 'success' | 'warning' | 'error'> = {
  base: 'neutral',
  build: 'info',
  peak: 'success',
  taper: 'warning',
  transition: 'error',
};

const STATUS_OPTIONS: { value: PlanStatus; label: string }[] = [
  { value: 'draft', label: 'Entwurf' },
  { value: 'active', label: 'Aktiv' },
  { value: 'completed', label: 'Abgeschlossen' },
  { value: 'paused', label: 'Pausiert' },
];

interface PhaseForm {
  id?: number;
  name: string;
  phase_type: PhaseType;
  start_week: number;
  end_week: number;
  notes: string;
  weekly_volume_min: string;
  weekly_volume_max: string;
  quality_sessions_per_week: string;
  strength_sessions_per_week: string;
  weekly_template: PhaseWeeklyTemplate | null;
}

export function TrainingPlanEditorPage() {
  const navigate = useNavigate();
  const { planId } = useParams<{ planId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const isEdit = !!planId;

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [targetEventDate, setTargetEventDate] = useState<Date | undefined>(undefined);
  const [status, setStatus] = useState<PlanStatus>('draft');
  const [goalId, setGoalId] = useState<number | undefined>(undefined);
  const [phases, setPhases] = useState<PhaseForm[]>([]);

  // UI state
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [generating, setGenerating] = useState(false);

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
      setName(plan.name);
      setDescription(plan.description ?? '');
      setStartDate(new Date(plan.start_date));
      setEndDate(new Date(plan.end_date));
      if (plan.target_event_date) setTargetEventDate(new Date(plan.target_event_date));
      setStatus(plan.status);
      if (plan.goal_id) setGoalId(plan.goal_id);
      setPhases(
        plan.phases.map((p) => ({
          id: p.id,
          name: p.name,
          phase_type: p.phase_type,
          start_week: p.start_week,
          end_week: p.end_week,
          notes: p.notes ?? '',
          weekly_volume_min: p.target_metrics?.weekly_volume_min?.toString() ?? '',
          weekly_volume_max: p.target_metrics?.weekly_volume_max?.toString() ?? '',
          quality_sessions_per_week: p.target_metrics?.quality_sessions_per_week?.toString() ?? '',
          strength_sessions_per_week:
            p.target_metrics?.strength_sessions_per_week?.toString() ?? '',
          weekly_template: p.weekly_template ?? null,
        })),
      );
    } catch {
      toast({ title: 'Plan konnte nicht geladen werden', variant: 'error' });
      navigate('/settings/plans');
    } finally {
      setLoading(false);
    }
  }, [planId, toast, navigate]);

  useEffect(() => {
    if (isEdit) loadPlan();
  }, [isEdit, loadPlan]);

  const handleSave = async () => {
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
        // Update plan metadata
        await updateTrainingPlan(parseInt(planId!, 10), {
          name: name.trim(),
          description: description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: targetEventDate ? formatDate(targetEventDate) : undefined,
          status,
          goal_id: goalId,
        });

        // Sync phases: update existing, add new, delete removed
        const plan = await getTrainingPlan(parseInt(planId!, 10));
        const existingPhaseIds = new Set(plan.phases.map((p) => p.id));
        const currentPhaseIds = new Set(phases.filter((p) => p.id).map((p) => p.id!));

        // Delete removed phases
        for (const ep of plan.phases) {
          if (!currentPhaseIds.has(ep.id)) {
            await deletePhase(parseInt(planId!, 10), ep.id);
          }
        }

        // Update or create phases
        for (const phase of phases) {
          const phaseData = phaseFormToParams(phase);

          if (phase.id && existingPhaseIds.has(phase.id)) {
            await updatePhase(parseInt(planId!, 10), phase.id, phaseData);
          } else {
            await addPhase(parseInt(planId!, 10), phaseData);
          }
        }

        toast({ title: 'Trainingsplan aktualisiert', variant: 'success' });
      } else {
        // Create new plan with phases
        await createTrainingPlan({
          name: name.trim(),
          description: description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: targetEventDate ? formatDate(targetEventDate) : undefined,
          status,
          goal_id: goalId,
          phases: phases.map(phaseFormToParams),
        });
        toast({ title: 'Trainingsplan erstellt', variant: 'success' });
      }
      navigate('/settings/plans');
    } catch {
      setError('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!planId) return;
    setDeleting(true);
    try {
      await deleteTrainingPlan(parseInt(planId, 10));
      toast({ title: 'Trainingsplan gelöscht', variant: 'success' });
      navigate('/settings/plans');
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  const handleGenerate = async () => {
    if (!planId) return;
    setGenerating(true);
    try {
      const result = await generateWeeklyPlans(parseInt(planId, 10));
      toast({
        title: `${result.weeks_generated} Wochenpläne erstellt`,
        variant: 'success',
      });
    } catch {
      toast({ title: 'Generierung fehlgeschlagen', variant: 'error' });
    } finally {
      setGenerating(false);
      setShowGenerateDialog(false);
    }
  };

  const phaseFormToParams = (phase: PhaseForm): TrainingPhaseCreateParams => {
    const volMin = phase.weekly_volume_min ? parseFloat(phase.weekly_volume_min) : undefined;
    const volMax = phase.weekly_volume_max ? parseFloat(phase.weekly_volume_max) : undefined;
    const quality = phase.quality_sessions_per_week
      ? parseInt(phase.quality_sessions_per_week, 10)
      : undefined;
    const strength = phase.strength_sessions_per_week
      ? parseInt(phase.strength_sessions_per_week, 10)
      : undefined;
    const hasMetrics =
      volMin !== undefined ||
      volMax !== undefined ||
      quality !== undefined ||
      strength !== undefined;

    return {
      name: phase.name,
      phase_type: phase.phase_type,
      start_week: phase.start_week,
      end_week: phase.end_week,
      notes: phase.notes || undefined,
      target_metrics: hasMetrics
        ? {
            weekly_volume_min: volMin,
            weekly_volume_max: volMax,
            quality_sessions_per_week: quality,
            strength_sessions_per_week: strength,
          }
        : undefined,
      weekly_template: phase.weekly_template ?? undefined,
    };
  };

  const addNewPhase = () => {
    const lastEnd = phases.length > 0 ? phases[phases.length - 1].end_week : 0;
    setPhases([
      ...phases,
      {
        name: `Phase ${phases.length + 1}`,
        phase_type: 'base',
        start_week: lastEnd + 1,
        end_week: lastEnd + 4,
        notes: '',
        weekly_volume_min: '',
        weekly_volume_max: '',
        quality_sessions_per_week: '',
        strength_sessions_per_week: '',
        weekly_template: null,
      },
    ]);
  };

  const updatePhaseForm = (idx: number, updates: Partial<PhaseForm>) => {
    setPhases(phases.map((p, i) => (i === idx ? { ...p, ...updates } : p)));
  };

  const removePhase = (idx: number) => {
    setPhases(phases.filter((_, i) => i !== idx));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/settings/plans" className="hover:underline underline-offset-2">
              Trainingspläne
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>
            {isEdit ? name || 'Plan bearbeiten' : 'Neuer Plan'}
          </BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex flex-wrap items-start justify-between gap-x-3 gap-y-2">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              {isEdit ? 'Plan bearbeiten' : 'Neuer Trainingsplan'}
            </h1>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate('/settings/plans')}>
              <ArrowLeft className="w-4 h-4 mr-1" />
              Zurück
            </Button>
            {isEdit && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDeleteDialog(true)}
                className="text-[var(--color-text-error)]"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </header>
      </div>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Trainingsplan löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              „{name}" und alle Phasen werden unwiderruflich gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={deleting}>
              {deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Generate Dialog */}
      <AlertDialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wochenpläne generieren?</AlertDialogTitle>
            <AlertDialogDescription>
              Alle bestehenden generierten Einträge dieses Plans werden ersetzt.
              {phases.length > 0
                ? ` ${phases.reduce((max, p) => Math.max(max, p.end_week), 0)} Wochen werden neu erstellt.`
                : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleGenerate} disabled={generating}>
              {generating ? <Spinner size="sm" /> : 'Generieren'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Plan Details */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="plan-name">Name</Label>
              <Input
                id="plan-name"
                placeholder="z.B. HM Sub-2h Vorbereitung"
                value={name}
                onChange={(e) => setName(e.target.value)}
                inputSize="sm"
                autoFocus
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="plan-description">Beschreibung</Label>
              <Input
                id="plan-description"
                placeholder="Kurze Beschreibung des Plans"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                inputSize="sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label>Startdatum</Label>
                <DatePicker value={startDate} onChange={setStartDate} inputSize="sm" />
              </div>
              <div className="space-y-1.5">
                <Label>Enddatum</Label>
                <DatePicker value={endDate} onChange={setEndDate} inputSize="sm" />
              </div>
              <div className="space-y-1.5">
                <Label>Wettkampf-Datum</Label>
                <DatePicker value={targetEventDate} onChange={setTargetEventDate} inputSize="sm" />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Status</Label>
                <Select
                  options={STATUS_OPTIONS}
                  value={status}
                  onChange={(v) => {
                    if (v) setStatus(v as PlanStatus);
                  }}
                  inputSize="sm"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Wettkampf-Ziel (optional)</Label>
                <Select
                  options={[
                    { value: '', label: 'Kein Ziel' },
                    ...goals.map((g) => ({ value: g.id.toString(), label: g.title })),
                  ]}
                  value={goalId?.toString() ?? ''}
                  onChange={(v) => setGoalId(v ? parseInt(v, 10) : undefined)}
                  inputSize="sm"
                  placeholder="Kein Ziel"
                />
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Phases */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Phasen ({phases.length})
            </h2>
            <Button variant="ghost" size="sm" onClick={addNewPhase}>
              <Plus className="w-4 h-4 mr-1" />
              Phase hinzufügen
            </Button>
          </div>

          {phases.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
              Noch keine Phasen. Füge deine erste Trainingsphase hinzu.
            </p>
          ) : (
            <div className="space-y-3">
              {phases.map((phase, idx) => (
                <div
                  key={phase.id ?? `new-${idx}`}
                  className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] p-3 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <Badge variant={PHASE_COLORS[phase.phase_type]} size="sm">
                      {PHASE_TYPES.find((t) => t.value === phase.phase_type)?.label ??
                        phase.phase_type}
                    </Badge>
                    <button
                      type="button"
                      onClick={() => removePhase(idx)}
                      className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-[var(--radius-component-sm)] text-[var(--color-text-muted)] hover:text-[var(--color-text-error)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                      aria-label="Phase entfernen"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label>Name</Label>
                      <Input
                        value={phase.name}
                        onChange={(e) => updatePhaseForm(idx, { name: e.target.value })}
                        inputSize="sm"
                        placeholder="z.B. Grundlagenaufbau"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Typ</Label>
                      <Select
                        options={PHASE_TYPES}
                        value={phase.phase_type}
                        onChange={(v) => {
                          if (v) updatePhaseForm(idx, { phase_type: v as PhaseType });
                        }}
                        inputSize="sm"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label>Von Woche</Label>
                      <Input
                        type="number"
                        min={1}
                        max={52}
                        value={phase.start_week}
                        onChange={(e) =>
                          updatePhaseForm(idx, { start_week: parseInt(e.target.value, 10) || 1 })
                        }
                        inputSize="sm"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Bis Woche</Label>
                      <Input
                        type="number"
                        min={1}
                        max={52}
                        value={phase.end_week}
                        onChange={(e) =>
                          updatePhaseForm(idx, { end_week: parseInt(e.target.value, 10) || 1 })
                        }
                        inputSize="sm"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label>Notizen</Label>
                    <Input
                      value={phase.notes}
                      onChange={(e) => updatePhaseForm(idx, { notes: e.target.value })}
                      inputSize="sm"
                      placeholder="Optionale Hinweise zur Phase"
                    />
                  </div>

                  {/* Target Metrics */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="space-y-1">
                      <Label>Vol. min (km)</Label>
                      <Input
                        type="number"
                        min={0}
                        step={5}
                        value={phase.weekly_volume_min}
                        onChange={(e) =>
                          updatePhaseForm(idx, { weekly_volume_min: e.target.value })
                        }
                        inputSize="sm"
                        placeholder="z.B. 30"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Vol. max (km)</Label>
                      <Input
                        type="number"
                        min={0}
                        step={5}
                        value={phase.weekly_volume_max}
                        onChange={(e) =>
                          updatePhaseForm(idx, { weekly_volume_max: e.target.value })
                        }
                        inputSize="sm"
                        placeholder="z.B. 45"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Quality/Wo.</Label>
                      <Input
                        type="number"
                        min={0}
                        max={5}
                        value={phase.quality_sessions_per_week}
                        onChange={(e) =>
                          updatePhaseForm(idx, { quality_sessions_per_week: e.target.value })
                        }
                        inputSize="sm"
                        placeholder="z.B. 2"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Kraft/Wo.</Label>
                      <Input
                        type="number"
                        min={0}
                        max={5}
                        value={phase.strength_sessions_per_week}
                        onChange={(e) =>
                          updatePhaseForm(idx, { strength_sessions_per_week: e.target.value })
                        }
                        inputSize="sm"
                        placeholder="z.B. 2"
                      />
                    </div>
                  </div>

                  {/* Weekly Template */}
                  <PhaseWeeklyTemplateEditor
                    template={phase.weekly_template}
                    phaseType={phase.phase_type}
                    onChange={(t) => updatePhaseForm(idx, { weekly_template: t })}
                  />
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Error + Save */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap justify-end gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/settings/plans')}>
          Abbrechen
        </Button>
        {isEdit && phases.length > 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowGenerateDialog(true)}
            disabled={generating}
          >
            <CalendarPlus className="w-4 h-4 mr-1" />
            Wochenpläne generieren
          </Button>
        )}
        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
          {saving ? (
            <Spinner size="sm" aria-hidden="true" />
          ) : (
            <>
              <Save className="w-4 h-4 mr-1" />
              {isEdit ? 'Speichern' : 'Erstellen'}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
