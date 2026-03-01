import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Badge,
  Spinner,
  EmptyState,
  useToast,
  Breadcrumbs,
  BreadcrumbItem,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import { Plus, ChevronRight, EllipsisVertical, Trash2, CalendarRange, Upload, CalendarPlus } from 'lucide-react';
import { listTrainingPlans, deleteTrainingPlan, importTrainingPlanYaml, generateWeeklyPlans } from '@/api/training-plans';
import type { TrainingPlanSummary } from '@/api/training-plans';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Entwurf',
  active: 'Aktiv',
  completed: 'Abgeschlossen',
  paused: 'Pausiert',
};

const STATUS_VARIANTS: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  active: 'info',
  completed: 'success',
  paused: 'warning',
};

export function TrainingPlansPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [plans, setPlans] = useState<TrainingPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleDelete = async (planId: number, name: string) => {
    try {
      await deleteTrainingPlan(planId);
      toast({ title: `„${name}" gelöscht`, variant: 'success' });
      await loadPlans();
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    }
  };

  const handleGenerate = async (planId: number, planName: string) => {
    try {
      const result = await generateWeeklyPlans(planId);
      toast({
        title: `${result.weeks_generated} Wochenpläne erstellt`,
        description: `für „${planName}"`,
        variant: 'success',
      });
    } catch {
      toast({ title: 'Generierung fehlgeschlagen', variant: 'error' });
    }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    setImporting(true);
    try {
      const plan = await importTrainingPlanYaml(file);
      toast({ title: `„${plan.name}" importiert`, variant: 'success' });
      navigate(`/settings/plans/${plan.id}`);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Import fehlgeschlagen';
      toast({ title: message, variant: 'error' });
    } finally {
      setImporting(false);
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('de-DE', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Trainingspläne</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex flex-wrap items-start justify-between gap-y-3">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              Trainingspläne
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Periodisierte Trainingspläne erstellen und verwalten.
            </p>
          </div>
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".yaml,.yml"
              onChange={handleImportFile}
              className="hidden"
              aria-hidden="true"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
            >
              {importing ? (
                <Spinner size="sm" aria-hidden="true" />
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-1" />
                  Importieren
                </>
              )}
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/settings/plans/new')}
            >
              <Plus className="w-4 h-4 mr-1" />
              Neuer Plan
            </Button>
          </div>
        </header>
      </div>

      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Pläne ({plans.length})
          </h2>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : plans.length === 0 ? (
            <EmptyState
              title="Noch keine Trainingspläne"
              description="Erstelle deinen ersten periodisierten Trainingsplan."
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/settings/plans/new')}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Plan erstellen
                </Button>
              }
            />
          ) : (
            <div className="space-y-1">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className="flex items-center gap-3 py-2.5 px-3 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                >
                  <CalendarRange className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />

                  <button
                    type="button"
                    onClick={() => navigate(`/settings/plans/${plan.id}`)}
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

                  <Badge variant={STATUS_VARIANTS[plan.status] ?? 'neutral'} size="sm">
                    {STATUS_LABELS[plan.status] ?? plan.status}
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
                      {plan.phase_count > 0 && (
                        <DropdownMenuItem
                          icon={<CalendarPlus />}
                          onSelect={() => handleGenerate(plan.id, plan.name)}
                        >
                          Wochenpläne generieren
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem
                        icon={<Trash2 />}
                        onSelect={() => handleDelete(plan.id, plan.name)}
                        className="text-[var(--color-text-error)]"
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
    </div>
  );
}
