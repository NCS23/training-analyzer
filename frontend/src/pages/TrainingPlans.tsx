import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Badge,
  Spinner,
  EmptyState,
  useToast,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  Label,
  Select,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  Checkbox,
} from '@nordlig/components';
import {
  Plus,
  EllipsisVertical,
  Trash2,
  CalendarRange,
  Upload,
  CalendarPlus,
  Pencil,
  Eye,
} from 'lucide-react';
import {
  listTrainingPlans,
  deleteTrainingPlan,
  importTrainingPlanYaml,
  validateTrainingPlanYaml,
  generateWeeklyPlans,
  getGenerationPreview,
} from '@/api/training-plans';
import type {
  TrainingPlanSummary,
  GenerationPreviewResponse,
  YamlValidationResult,
} from '@/api/training-plans';
import { YamlValidationResultPanel } from '@/components/YamlValidationResult';
import { STATUS_OPTIONS, STATUS_BADGE_VARIANTS } from '@/components/plan-helpers';

export function TrainingPlansPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [plans, setPlans] = useState<TrainingPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [generatingPlan, setGeneratingPlan] = useState<{ id: number; name: string } | null>(null);
  const [genPreview, setGenPreview] = useState<GenerationPreviewResponse | null>(null);
  const [genStrategy, setGenStrategy] = useState<'all' | 'unedited_only'>('all');
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<YamlValidationResult | null>(null);
  const [pendingImportFile, setPendingImportFile] = useState<File | null>(null);
  const [showValidationDialog, setShowValidationDialog] = useState(false);
  const [exerciseReplacements, setExerciseReplacements] = useState<Record<string, string>>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingPlan, setDeletingPlan] = useState<TrainingPlanSummary | null>(null);
  const [deleteWeeklyPlans, setDeleteWeeklyPlans] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadPlans = useCallback(async () => {
    try {
      setLoading(true);
      const result = await listTrainingPlans();
      setPlans(result.plans);
    } catch {
      toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  const openDeleteDialog = (plan: TrainingPlanSummary) => {
    setDeletingPlan(plan);
    setDeleteWeeklyPlans(false);
    setShowDeleteDialog(true);
  };

  const handleDelete = async () => {
    if (!deletingPlan) return;
    setDeleting(true);
    try {
      await deleteTrainingPlan(deletingPlan.id, deleteWeeklyPlans);
      toast({ title: `„${deletingPlan.name}" gelöscht`, variant: 'success' });
      await loadPlans();
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
      setDeletingPlan(null);
    }
  };

  const handleGenerateClick = async (planId: number, planName: string) => {
    try {
      const previewData = await getGenerationPreview(planId);
      if (previewData.edited_week_count > 0) {
        setGeneratingPlan({ id: planId, name: planName });
        setGenPreview(previewData);
        setGenStrategy('unedited_only');
        setShowGenerateDialog(true);
        return;
      }
    } catch {
      // Fallback: generate directly
    }
    await handleGenerateConfirm(planId, planName, 'all');
  };

  const handleGenerateConfirm = async (
    planId: number,
    planName: string,
    strategy: 'all' | 'unedited_only',
  ) => {
    setGenerating(true);
    try {
      const result = await generateWeeklyPlans(planId, strategy);
      toast({
        title: `${result.weeks_generated} Wochenpläne erstellt`,
        description: `für „${planName}"`,
        variant: 'success',
      });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast({ title: detail ?? 'Generierung fehlgeschlagen', variant: 'error' });
    } finally {
      setGenerating(false);
      setShowGenerateDialog(false);
      setGeneratingPlan(null);
    }
  };

  const doImport = async (file: File) => {
    setImporting(true);
    try {
      // Filter out empty replacements (user chose "Neu erstellen")
      const activeReplacements = Object.fromEntries(
        Object.entries(exerciseReplacements).filter(([, v]) => v.length > 0),
      );
      const plan = await importTrainingPlanYaml(file, activeReplacements);

      // Show toast for auto-created exercises
      const unknowns = validationResult?.unknown_exercises ?? [];
      const created = unknowns.filter((ex) => !activeReplacements[ex.exercise_name]);
      if (created.length > 0) {
        toast({
          title: `${created.length} neue Übung${created.length > 1 ? 'en' : ''} erstellt`,
          description: created.map((ex) => ex.exercise_name).join(', '),
          variant: 'info',
        });
      }

      toast({ title: `„${plan.name}" importiert`, variant: 'success' });
      navigate(`/plan/programs/${plan.id}`);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Import fehlgeschlagen';
      toast({ title: message, variant: 'error' });
    } finally {
      setImporting(false);
    }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setExerciseReplacements({});
    setValidating(true);
    try {
      const result = await validateTrainingPlanYaml(file);
      const hasIssues =
        result.errors.length > 0 ||
        result.warnings.length > 0 ||
        result.unknown_exercises.length > 0;
      if (!hasIssues) {
        await doImport(file);
      } else {
        setPendingImportFile(file);
        setValidationResult(result);
        setShowValidationDialog(true);
      }
    } catch {
      toast({ title: 'Validierung fehlgeschlagen', variant: 'error' });
    } finally {
      setValidating(false);
    }
  };

  const handleValidationConfirm = async () => {
    if (!pendingImportFile) return;
    setShowValidationDialog(false);
    await doImport(pendingImportFile);
    setPendingImportFile(null);
    setValidationResult(null);
  };

  const handleValidationCancel = () => {
    setShowValidationDialog(false);
    setPendingImportFile(null);
    setValidationResult(null);
    setExerciseReplacements({});
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('de-DE', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".yaml,.yml"
        onChange={handleImportFile}
        className="hidden"
        aria-hidden="true"
      />

      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
              Programme ({plans.length})
            </h2>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  aria-label="Aktionen"
                  className="inline-flex items-center justify-center w-8 h-8 rounded-[var(--radius-interactive)] text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] hover:bg-[var(--color-bg-subtle)] transition-colors duration-150 motion-reduce:transition-none cursor-pointer"
                >
                  <EllipsisVertical className="w-4 h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem icon={<Plus />} onSelect={() => navigate('/plan/programs/new')}>
                  Neuer Plan
                </DropdownMenuItem>
                <DropdownMenuItem
                  icon={<Upload />}
                  onSelect={() => fileInputRef.current?.click()}
                  disabled={importing || validating}
                >
                  YAML importieren
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : plans.length === 0 ? (
            <EmptyState
              title="Noch keine Trainingspläne"
              description="Erstelle deinen ersten periodisierten Trainingsplan."
              action={
                <Button variant="primary" size="sm" onClick={() => navigate('/plan/programs/new')}>
                  <Plus className="w-4 h-4 mr-1" />
                  Plan erstellen
                </Button>
              }
            />
          ) : (
            <div className="space-y-3">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className="flex items-center gap-3 p-3 rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)] transition-colors motion-reduce:transition-none"
                >
                  <CalendarRange className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />

                  <button
                    type="button"
                    onClick={() => navigate(`/plan/programs/${plan.id}`)}
                    className="flex-1 min-w-0 text-left"
                    aria-label={`${plan.name} bearbeiten`}
                  >
                    <span className="text-sm font-medium text-[var(--color-text-base)] truncate block">
                      {plan.name}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {formatDate(plan.start_date)} – {formatDate(plan.end_date)}
                      {plan.phase_count > 0 && ` · ${plan.phase_count} Phasen`}
                      {plan.goal_title && ` · ${plan.goal_title}`}
                    </span>
                  </button>

                  <Badge variant={STATUS_BADGE_VARIANTS[plan.status] ?? 'neutral'} size="sm">
                    {STATUS_OPTIONS.find((s) => s.value === plan.status)?.label ?? plan.status}
                  </Badge>

                  <DropdownMenu>
                    <DropdownMenuTrigger>
                      <button
                        type="button"
                        className="shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-[var(--radius-component-sm)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                        aria-label="Aktionen"
                      >
                        <EllipsisVertical className="w-4 h-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        icon={<Eye />}
                        onSelect={() => navigate(`/plan/programs/${plan.id}`)}
                      >
                        Anzeigen
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        icon={<Pencil />}
                        onSelect={() => navigate(`/plan/programs/${plan.id}?edit=true`)}
                      >
                        Bearbeiten
                      </DropdownMenuItem>
                      {plan.phase_count > 0 && (
                        <DropdownMenuItem
                          icon={<CalendarPlus />}
                          onSelect={() => handleGenerateClick(plan.id, plan.name)}
                        >
                          Wochenpläne generieren
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        icon={<Trash2 />}
                        destructive
                        onSelect={() => openDeleteDialog(plan)}
                      >
                        Löschen
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Generate Strategy Dialog */}
      <AlertDialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wochenpläne generieren?</AlertDialogTitle>
            <AlertDialogDescription>
              {genPreview && genPreview.edited_week_count > 0 && (
                <>
                  <span className="font-medium text-[var(--color-text-warning)]">
                    {genPreview.edited_week_count} von {genPreview.total_generated_weeks} Wochen
                  </span>{' '}
                  für „{generatingPlan?.name}" wurden manuell bearbeitet.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>

          {genPreview && genPreview.edited_week_count > 0 && (
            <div className="space-y-2 px-[var(--spacing-md)]">
              <Label>Strategie</Label>
              <Select
                options={[
                  {
                    value: 'unedited_only',
                    label: `Nur unbearbeitete Wochen (${genPreview.unedited_week_count})`,
                  },
                  {
                    value: 'all',
                    label: `Alle Wochen überschreiben (${genPreview.total_generated_weeks})`,
                  },
                ]}
                value={genStrategy}
                onChange={(v) => {
                  if (v) setGenStrategy(v as 'all' | 'unedited_only');
                }}
                inputSize="sm"
              />
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (generatingPlan) {
                  handleGenerateConfirm(generatingPlan.id, generatingPlan.name, genStrategy);
                }
              }}
              disabled={generating}
            >
              {generating ? <Spinner size="sm" /> : 'Generieren'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Trainingsplan löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              „{deletingPlan?.name}" und alle Phasen werden unwiderruflich gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {deletingPlan && deletingPlan.weekly_plan_week_count > 0 && (
            <div className="px-[var(--spacing-md)]">
              <label className="inline-flex items-center gap-2 cursor-pointer min-h-[44px]">
                <Checkbox
                  checked={deleteWeeklyPlans}
                  onCheckedChange={(checked) => setDeleteWeeklyPlans(checked === true)}
                />
                <span className="text-sm text-[var(--color-text-base)]">
                  {deletingPlan.weekly_plan_week_count} Wochenpläne ebenfalls löschen
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

      {/* YAML Validation Dialog */}
      <AlertDialog open={showValidationDialog} onOpenChange={handleValidationCancel}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>YAML-Validierung</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div>
                {validationResult && pendingImportFile && (
                  <YamlValidationResultPanel
                    result={validationResult}
                    filename={pendingImportFile.name}
                    exerciseReplacements={exerciseReplacements}
                    onExerciseReplacementChange={(original, replacement) =>
                      setExerciseReplacements((prev) => ({
                        ...prev,
                        [original]: replacement,
                      }))
                    }
                  />
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleValidationConfirm}
              disabled={!validationResult?.valid || importing}
            >
              {importing ? <Spinner size="sm" /> : 'Trotzdem importieren'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
