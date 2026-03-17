import { useNavigate } from 'react-router-dom';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import {
  Card,
  CardBody,
  Button,
  Spinner,
  Alert,
  AlertDescription,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  Footprints,
  Minus,
  Moon,
  Save,
  EllipsisVertical,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
} from 'lucide-react';
import { formatTonnage } from '@/hooks/useTonnageCalc';
import { RUN_TYPE_LABELS } from '@/constants/plan';
import { DayCard } from '@/components/day-card';
import { SyncToPlanBar } from '@/components/SyncToPlanBar';
import { SaveWeeklyPlanDialog } from '@/components/SaveWeeklyPlanDialog';
import { WeeklyReviewSection } from '@/components/WeeklyReviewSection';
import { useWeeklyPlan } from '@/hooks/useWeeklyPlan';
import { useWeeklyPlanDragDrop } from '@/hooks/useWeeklyPlanDragDrop';
import { formatDateRange, categoryLabel } from '@/utils/weeklyPlanUtils';

// eslint-disable-next-line max-lines-per-function, complexity -- JSX-heavy page component
export function WeeklyPlanPage() {
  const navigate = useNavigate();
  const plan = useWeeklyPlan();
  const dnd = useWeeklyPlanDragDrop({
    entries: plan.entries,
    onMoveSession: plan.handleMoveSession,
    onMoveRestDay: plan.handleMoveRestDay,
  });

  return (
    <div className="space-y-4">
      {plan.error && (
        <Alert variant="error">
          <AlertDescription>{plan.error}</AlertDescription>
        </Alert>
      )}

      {/* Week Navigation + Stats */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">Wochenplan</h2>
            {plan.hasContent && (
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
                  <DropdownMenuItem
                    icon={<Trash2 />}
                    destructive
                    onSelect={() => plan.setShowDeleteDialog(true)}
                  >
                    Woche löschen
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => plan.navigateWeek(-1)}
              aria-label="Vorherige Woche"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <div className="text-center flex-1 min-w-0">
              <p className="text-sm font-semibold text-[var(--color-text-base)]">
                {formatDateRange(plan.weekStart)}
              </p>
              {!plan.isCurrentWeek && (
                <button
                  type="button"
                  onClick={plan.goToCurrentWeek}
                  className="text-xs text-[var(--color-text-link)] hover:underline mt-0.5 min-h-[28px]"
                >
                  Aktuelle Woche
                </button>
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => plan.navigateWeek(1)}
              aria-label="Nächste Woche"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          {/* Stats row */}
          {(plan.stats.strength > 0 || plan.stats.running > 0) && (
            <div className="flex items-center justify-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
              {plan.stats.running > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Footprints className="w-3 h-3" /> {plan.stats.running}× Laufen
                  {plan.stats.totalMinutes > 0 && (
                    <span className="text-[var(--color-text-base)] font-medium ml-0.5">
                      ({Math.round(plan.stats.totalMinutes)} min)
                    </span>
                  )}
                </span>
              )}
              {plan.stats.strength > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Dumbbell className="w-3 h-3" /> {plan.stats.strength}× Kraft
                  {plan.compliance?.strength_summary &&
                    plan.compliance.strength_summary.total_tonnage_kg > 0 &&
                    (() => {
                      const ss = plan.compliance.strength_summary;
                      const fmt = formatTonnage(ss.total_tonnage_kg);
                      return (
                        <>
                          <span className="text-[var(--color-text-base)] font-medium ml-0.5">
                            ({fmt.value}
                            <span className="text-[var(--color-text-muted)] font-normal">
                              {fmt.unit}
                            </span>
                            )
                          </span>
                          {ss.tonnage_delta_kg != null && ss.trend && (
                            <span
                              className={`inline-flex items-center gap-0.5 ml-0.5 font-medium ${
                                ss.trend === 'up'
                                  ? 'text-[var(--color-text-success)]'
                                  : ss.trend === 'down'
                                    ? 'text-[var(--color-text-error)]'
                                    : 'text-[var(--color-text-muted)]'
                              }`}
                            >
                              {ss.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                              {ss.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                              {ss.trend === 'stable' && <Minus className="w-3 h-3" />}
                              {ss.tonnage_delta_kg > 0 ? '+' : ''}
                              {Math.round(ss.tonnage_delta_kg)}kg
                            </span>
                          )}
                        </>
                      );
                    })()}
                </span>
              )}
              {plan.stats.rest > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Moon className="w-3 h-3" /> {plan.stats.rest}× Ruhe
                </span>
              )}
            </div>
          )}

          {/* Category breakdown row */}
          {plan.compliance?.strength_summary &&
            plan.compliance.strength_summary.categories.length > 0 && (
              <div className="flex items-center justify-center gap-3 mt-1.5 text-[10px] text-[var(--color-text-muted)]">
                {plan.compliance.strength_summary.categories.map((cat) => {
                  const fmt = formatTonnage(cat.tonnage_kg);
                  return (
                    <span key={cat.category} className="inline-flex items-center gap-1">
                      <span className="capitalize">{categoryLabel(cat.category)}</span>
                      <span className="font-medium text-[var(--color-text-base)]">
                        {fmt.value}
                        <span className="text-[var(--color-text-muted)] font-normal">
                          {fmt.unit}
                        </span>
                      </span>
                    </span>
                  );
                })}
              </div>
            )}

          {/* Compliance bar — session-level progress */}
          {plan.compliance &&
            (() => {
              let planned = 0;
              let completed = 0;
              for (const ce of plan.compliance.entries) {
                if (ce.is_rest_day) {
                  planned++;
                  if (ce.status === 'rest_ok') completed++;
                } else {
                  const types = ce.planned_types;
                  planned += types.length;
                  for (const pt of types) {
                    if (ce.actual_sessions.some((a) => a.workout_type === pt)) {
                      completed++;
                    }
                  }
                }
              }
              if (planned === 0) return null;
              return (
                <div className="mt-3 pt-5 border-t border-[var(--color-border-muted)]">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-[var(--color-text-muted)]">Umsetzung</p>
                    <p className="text-xs font-medium text-[var(--color-text-base)]">
                      {completed}/{planned}
                    </p>
                  </div>
                  <div className="mt-1.5 h-2 rounded-full bg-[var(--color-border-muted)] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-[var(--color-interactive-primary)] transition-all duration-500 motion-reduce:transition-none"
                      style={{
                        width: `${Math.round((completed / planned) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })()}
          {/* Day grid */}
          <div className="mt-10">
            {plan.loading ? (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            ) : (
              <DndContext
                sensors={dnd.sensors}
                onDragStart={dnd.handleDragStart}
                onDragEnd={dnd.handleDragEnd}
              >
                <div
                  className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-[var(--spacing-sm)]"
                  role="grid"
                  aria-label="Wochenplan"
                >
                  {plan.entries.map((entry) => {
                    const isToday =
                      plan.isCurrentWeek &&
                      new Date().getDay() === (entry.day_of_week === 6 ? 0 : entry.day_of_week + 1);
                    const dayCompliance = plan.compliance?.entries.find(
                      (c) => c.day_of_week === entry.day_of_week,
                    );

                    return (
                      <DayCard
                        key={entry.day_of_week}
                        entry={entry}
                        weekStart={plan.weekStart}
                        isToday={isToday}
                        compliance={dayCompliance}
                        showCompliance={plan.hasContent}
                        onUpdate={(updates) => plan.updateEntry(entry.day_of_week, updates)}
                        onNavigateSession={(id) => navigate(`/sessions/${id}`)}
                        onMoveSession={(sessionIdx, targetDay) =>
                          plan.handleMoveSession(entry.day_of_week, sessionIdx, targetDay)
                        }
                        onMoveRestDay={(targetDay) =>
                          plan.handleMoveRestDay(entry.day_of_week, targetDay)
                        }
                      />
                    );
                  })}
                </div>

                <DragOverlay>
                  {dnd.activeDragData?.type === 'rest' && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-paper)] shadow-[var(--shadow-raised)] border border-[var(--color-border-muted)]">
                      <Moon className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      <span className="text-xs font-medium text-[var(--color-text-base)]">
                        Ruhetag
                      </span>
                    </div>
                  )}
                  {dnd.activeDragSession && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-paper)] shadow-[var(--shadow-raised)] border border-[var(--color-border-muted)]">
                      {dnd.activeDragSession.training_type === 'strength' ? (
                        <Dumbbell className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      ) : (
                        <Footprints className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      )}
                      <span className="text-xs font-medium text-[var(--color-text-base)]">
                        {dnd.activeDragSession.training_type === 'strength'
                          ? (dnd.activeDragSession.template_name ?? 'Kraft')
                          : (RUN_TYPE_LABELS[
                              dnd.activeDragSession.run_details?.run_type ?? 'easy'
                            ] ?? 'Laufen')}
                      </span>
                    </div>
                  )}
                </DragOverlay>
              </DndContext>
            )}
          </div>
        </CardBody>
      </Card>

      {/* KI-Review */}
      <WeeklyReviewSection weekStart={plan.weekStart} />

      {/* Delete Dialog */}
      <AlertDialog open={plan.showDeleteDialog} onOpenChange={plan.setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wochenplan löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Alle Einträge für die Woche {formatDateRange(plan.weekStart)} werden gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={plan.handleDeleteWeek} disabled={plan.deleting}>
              {plan.deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Sync-to-Plan Bar */}
      {plan.showSyncBar && plan.linkedPlanId && plan.editedPlanCount > 0 && (
        <SyncToPlanBar
          planId={plan.linkedPlanId}
          weekStart={plan.weekStart}
          editedCount={plan.editedPlanCount}
          onSynced={() => {
            plan.setShowSyncBar(false);
            plan.loadWeek(plan.weekStart);
          }}
          onDismiss={() => plan.setShowSyncBar(false)}
        />
      )}

      {/* Quick action */}
      <Button
        variant="secondary"
        size="sm"
        onClick={() => navigate('/sessions/new')}
        className="w-full"
      >
        <Upload className="w-4 h-4 mr-1" />
        Training hochladen
      </Button>

      {/* Save Dialog (plan-linked) */}
      <SaveWeeklyPlanDialog
        open={plan.showSaveDialog}
        onOpenChange={plan.setShowSaveDialog}
        onSaveWeekOnly={plan.handleSaveWeekOnly}
        onSaveAndSync={plan.handleSaveAndSync}
      />

      {/* Save button */}
      {plan.dirty && (
        <div className="sticky bottom-4 z-10">
          <Button
            variant="primary"
            onClick={plan.handleSaveClick}
            disabled={plan.saving}
            className="w-full"
            size="lg"
          >
            {plan.saving ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {plan.saving ? 'Speichern...' : 'Wochenplan speichern'}
          </Button>
        </div>
      )}
    </div>
  );
}
