import { useState, useEffect, useCallback } from 'react';
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
import {
  Plus,
  ChevronRight,
  EllipsisVertical,
  Copy,
  Trash2,
  ClipboardList,
  Footprints,
} from 'lucide-react';
import {
  listTrainingPlans,
  deleteTrainingPlan,
  duplicateTrainingPlan,
} from '@/api/training-plans';
import type { TrainingPlanSummary } from '@/api/training-plans';

export function TrainingPlansPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [plans, setPlans] = useState<TrainingPlanSummary[]>([]);
  const [loading, setLoading] = useState(true);

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
      toast({ title: `"${name}" gelöscht`, variant: 'success' });
      await loadPlans();
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    }
  };

  const handleDuplicate = async (planId: number) => {
    try {
      await duplicateTrainingPlan(planId);
      toast({ title: 'Plan dupliziert', variant: 'success' });
      await loadPlans();
    } catch {
      toast({ title: 'Duplizieren fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs + Header */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Trainingspläne</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              Trainingspläne
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Templates für Kraft- und Lauftraining erstellen und verwalten.
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/settings/plans/new')}
          >
            <Plus className="w-4 h-4 mr-1" />
            Neuer Plan
          </Button>
        </header>
      </div>

      {/* Plan List */}
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
              description="Erstelle deinen ersten Plan mit Übungen, Sätzen und Gewichten."
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
                  {plan.session_type === 'running' ? (
                    <Footprints className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  ) : (
                    <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  )}

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
                      {plan.session_type === 'running'
                        ? plan.run_type ?? 'Lauf-Template'
                        : `${plan.exercise_count} Übungen · ${plan.total_sets} Sätze`}
                    </span>
                  </button>

                  <Badge variant="neutral" size="sm">
                    {plan.session_type === 'strength' ? 'Kraft' : 'Laufen'}
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
                        icon={<Copy />}
                        onSelect={() => handleDuplicate(plan.id)}
                      >
                        Duplizieren
                      </DropdownMenuItem>
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
