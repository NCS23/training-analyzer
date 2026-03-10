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
  Checkbox,
  MultiSelect,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@nordlig/components';
import { Save, ChevronRight, Plus, Trash2, Pencil, EllipsisVertical } from 'lucide-react';
import {
  createTrainingPlan,
  getTrainingPlan,
  updateTrainingPlan,
  deleteTrainingPlan,
  addPhase,
  updatePhase,
  deletePhase,
} from '@/api/training-plans';
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
import { PhaseWeeklyTemplateEditor } from '@/components/PhaseWeeklyTemplateEditor';
import { PlanChangeLog } from '@/components/PlanChangeLog';
import { TrainingPlanReadView } from '@/components/TrainingPlanReadView';
import { PHASE_TYPES, STATUS_OPTIONS, STATUS_BADGE_VARIANTS } from '@/components/plan-helpers';
import { PHASE_FOCUS_TAGS, PHASE_FOCUS_DEFAULTS, normalizeFocusKey } from '@/constants/taxonomy';

interface PhaseForm {
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

export function TrainingPlanEditorPage() {
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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteWeeklyPlans, setDeleteWeeklyPlans] = useState(false);
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
        const updatedPlan = await updateTrainingPlan(parseInt(planId!, 10), {
          name: name.trim(),
          description: description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: targetEventDate ? formatDate(targetEventDate) : undefined,
          weekly_structure: restDays.length > 0 ? { rest_days: restDays } : undefined,
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
        let totalRegenerated = 0;
        let totalSkippedEdited = 0;
        for (const phase of phases) {
          const phaseData = phaseFormToParams(phase);

          if (phase.id && existingPhaseIds.has(phase.id)) {
            const result = await updatePhase(parseInt(planId!, 10), phase.id, phaseData);
            if (result.auto_regeneration) {
              totalRegenerated += result.auto_regeneration.weeks_regenerated;
              totalSkippedEdited += result.auto_regeneration.weeks_skipped_edited;
            }
          } else {
            await addPhase(parseInt(planId!, 10), phaseData);
          }
        }

        toast({ title: 'Trainingsplan aktualisiert', variant: 'success' });

        // Show auto-generation toast if weekly plans were generated
        if (updatedPlan.auto_generation_result) {
          const { weeks_generated } = updatedPlan.auto_generation_result;
          toast({
            title: `${weeks_generated} Wochenpläne automatisch erstellt`,
            variant: 'success',
          });
        }

        // Show auto-regeneration toast if template changes triggered regeneration
        if (totalRegenerated > 0) {
          const editedNote =
            totalSkippedEdited > 0 ? ` (${totalSkippedEdited} bearbeitete beibehalten)` : '';
          toast({
            title: `${totalRegenerated} Wochenpläne aktualisiert${editedNote}`,
            variant: 'success',
          });
        }
      } else {
        // Create new plan with phases
        await createTrainingPlan({
          name: name.trim(),
          description: description.trim() || undefined,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
          target_event_date: targetEventDate ? formatDate(targetEventDate) : undefined,
          weekly_structure: restDays.length > 0 ? { rest_days: restDays } : undefined,
          status,
          goal_id: goalId,
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
  };

  const handleDelete = async () => {
    if (!planId) return;
    setDeleting(true);
    try {
      await deleteTrainingPlan(parseInt(planId, 10), deleteWeeklyPlans);
      toast({ title: 'Trainingsplan gelöscht', variant: 'success' });
      navigate('/plan/programs');
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
      setDeleteWeeklyPlans(false);
    }
  };

  const phaseFormToParams = (phase: PhaseForm): TrainingPhaseCreateParams => {
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
  };

  const addNewPhase = () => {
    const lastEnd = phases.length > 0 ? phases[phases.length - 1].end_week : 0;
    const defaults = PHASE_FOCUS_DEFAULTS['base'];
    setPhases([
      ...phases,
      {
        name: `Phase ${phases.length + 1}`,
        phase_type: 'base',
        start_week: lastEnd + 1,
        end_week: lastEnd + 4,
        notes: '',
        focus_primary: [...defaults.primary],
        focus_secondary: [...defaults.secondary],
        weekly_template: null,
        weekly_templates: null,
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
    <div
      className={`p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6${isEditing ? ' pb-24' : ''}`}
    >
      {/* Breadcrumbs */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan" className="hover:underline underline-offset-2">
              Plan
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/programs" className="hover:underline underline-offset-2">
              Programme
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>{isEdit ? name || 'Plan' : 'Neuer Plan'}</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
              {!isEdit ? 'Neuer Trainingsplan' : isEditing ? 'Plan bearbeiten' : name}
            </h1>
            {isEdit && !isEditing && (
              <Badge variant={STATUS_BADGE_VARIANTS[status]} size="xs">
                {STATUS_OPTIONS.find((s) => s.value === status)?.label ?? status}
              </Badge>
            )}
          </div>
          {isEdit && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
                  <EllipsisVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  icon={<Pencil />}
                  disabled={isEditing}
                  onSelect={() => setEditMode(true)}
                >
                  Bearbeiten
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  icon={<Trash2 />}
                  destructive
                  onSelect={() => setShowDeleteDialog(true)}
                >
                  Löschen
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
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

          {weeklyPlanWeekCount > 0 && (
            <div className="px-[var(--spacing-md)]">
              <label className="inline-flex items-center gap-2 cursor-pointer min-h-[44px]">
                <Checkbox
                  checked={deleteWeeklyPlans}
                  onCheckedChange={(checked) => setDeleteWeeklyPlans(checked === true)}
                />
                <span className="text-sm text-[var(--color-text-base)]">
                  {weeklyPlanWeekCount} Wochenpläne ebenfalls löschen
                </span>
              </label>
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={deleting}>
              {deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Read-Only View */}
      {!isEditing && rawPlan && <TrainingPlanReadView plan={rawPlan} />}

      {/* Plan Details (Edit Mode) */}
      {isEditing && (
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Startdatum</Label>
                  <DatePicker value={startDate} onChange={setStartDate} inputSize="sm" />
                </div>
                <div className="space-y-1.5">
                  <Label>Enddatum</Label>
                  <DatePicker value={endDate} onChange={setEndDate} inputSize="sm" />
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
                  <Label>Ziel</Label>
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
      )}

      {/* Phases (Edit Mode) */}
      {isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-4">
              Phasen ({phases.length})
            </h2>

            {phases.length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
                Noch keine Phasen. Füge deine erste Trainingsphase hinzu.
              </p>
            ) : (
              <div className="space-y-3">
                {phases.map((phase, idx) => (
                  <div
                    key={phase.id ?? `new-${idx}`}
                    className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 pt-3 pb-6 space-y-3"
                  >
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
                            if (!v) return;
                            const newType = v as PhaseType;
                            const oldDefaults = PHASE_FOCUS_DEFAULTS[phase.phase_type];
                            const newDefaults = PHASE_FOCUS_DEFAULTS[newType];
                            // Auto-fill focus if empty or still at old defaults
                            const isPrimaryDefault =
                              phase.focus_primary.length === 0 ||
                              JSON.stringify([...phase.focus_primary].sort()) ===
                                JSON.stringify([...oldDefaults.primary].sort());
                            const isSecondaryDefault =
                              phase.focus_secondary.length === 0 ||
                              JSON.stringify([...phase.focus_secondary].sort()) ===
                                JSON.stringify([...oldDefaults.secondary].sort());
                            updatePhaseForm(idx, {
                              phase_type: newType,
                              ...(isPrimaryDefault && {
                                focus_primary: [...newDefaults.primary],
                              }),
                              ...(isSecondaryDefault && {
                                focus_secondary: [...newDefaults.secondary],
                              }),
                            });
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

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label>Primäre Schwerpunkte</Label>
                        <MultiSelect
                          options={PHASE_FOCUS_TAGS}
                          value={phase.focus_primary}
                          onChange={(values) => updatePhaseForm(idx, { focus_primary: values })}
                          placeholder="Schwerpunkte wählen…"
                          inputSize="sm"
                          aria-label="Primäre Schwerpunkte"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Sekundäre Schwerpunkte</Label>
                        <MultiSelect
                          options={PHASE_FOCUS_TAGS}
                          value={phase.focus_secondary}
                          onChange={(values) => updatePhaseForm(idx, { focus_secondary: values })}
                          placeholder="Schwerpunkte wählen…"
                          inputSize="sm"
                          badgeVariant="primary"
                          aria-label="Sekundäre Schwerpunkte"
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

                    {/* Weekly Template */}
                    <PhaseWeeklyTemplateEditor
                      template={phase.weekly_template}
                      weeklyTemplates={phase.weekly_templates}
                      phaseType={phase.phase_type}
                      startWeek={phase.start_week}
                      endWeek={phase.end_week}
                      onChange={(t) => updatePhaseForm(idx, { weekly_template: t })}
                      onChangeWeeklyTemplates={(wt) =>
                        updatePhaseForm(idx, { weekly_templates: wt })
                      }
                    />

                    <div className="flex justify-end pt-3">
                      <Button
                        variant="destructive-outline"
                        size="sm"
                        onClick={() => removePhase(idx)}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Phase entfernen
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <Button variant="ghost" size="sm" onClick={addNewPhase} className="w-full mt-2">
              <Plus className="w-4 h-4 mr-1" />
              Phase hinzufügen
            </Button>
          </CardBody>
        </Card>
      )}

      {/* Change Log */}
      {isEdit && planId && <PlanChangeLog planId={parseInt(planId, 10)} />}

      {/* Error — only in edit mode */}
      {isEditing && error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Fixed ActionBar — edit mode */}
      {isEditing && (
        <div
          role="toolbar"
          className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40 bg-[var(--color-actionbar-bg)] border-t border-[var(--color-actionbar-border)] rounded-t-[var(--radius-actionbar)] [box-shadow:var(--shadow-actionbar-default)] px-[var(--spacing-actionbar-padding-x)] py-[var(--spacing-actionbar-padding-y)] flex items-center justify-between gap-[var(--spacing-actionbar-gap)]"
        >
          <span className="text-xs text-[var(--color-actionbar-text)] hidden sm:inline">
            Ungespeicherte Änderungen
          </span>
          <div className="flex gap-2 ml-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (isEdit) {
                  setEditMode(false);
                  loadPlan();
                } else {
                  navigate('/plan/programs');
                }
              }}
            >
              Abbrechen
            </Button>
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
      )}
    </div>
  );
}
