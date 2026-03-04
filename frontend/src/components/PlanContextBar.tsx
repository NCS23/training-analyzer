import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Target } from 'lucide-react';
import { Card, CardBody, Popover, PopoverTrigger, PopoverContent } from '@nordlig/components';
import { getTrainingPlan } from '@/api/training-plans';
import type { TrainingPlan, TrainingPhase } from '@/api/training-plans';

// --- Phase Type Labels ---

const phaseTypeLabels: Record<string, string> = {
  base: 'Basis',
  build: 'Aufbau',
  peak: 'Spitze',
  taper: 'Tapering',
  transition: 'Übergang',
};

// --- Phase Timeline Colors (#153) ---

const phaseTimelineColors: Record<string, { filled: string; empty: string }> = {
  base: { filled: 'var(--color-text-muted)', empty: 'var(--color-border-muted)' },
  build: { filled: 'var(--color-interactive-primary)', empty: 'var(--color-bg-primary-subtle)' },
  peak: { filled: 'var(--color-text-primary)', empty: 'var(--color-bg-primary-muted)' },
  taper: { filled: 'var(--color-text-accent)', empty: 'var(--color-bg-accent-subtle)' },
  transition: { filled: 'var(--color-text-muted)', empty: 'var(--color-border-muted)' },
};

// --- Helpers ---

function getWeekNumber(planStartDate: string, weekStart: string): number {
  const planStart = new Date(planStartDate);
  const planStartMonday = new Date(planStart);
  planStartMonday.setDate(
    planStart.getDate() - planStart.getDay() + (planStart.getDay() === 0 ? -6 : 1),
  );

  const weekStartDate = new Date(weekStart);
  const diffMs = weekStartDate.getTime() - planStartMonday.getTime();
  return Math.floor(diffMs / (7 * 24 * 60 * 60 * 1000)) + 1;
}

function getCurrentPhase(phases: TrainingPhase[], weekNumber: number): TrainingPhase | null {
  return phases.find((p) => p.start_week <= weekNumber && weekNumber <= p.end_week) ?? null;
}

function getTotalWeeks(phases: TrainingPhase[]): number {
  if (phases.length === 0) return 0;
  return Math.max(...phases.map((p) => p.end_week));
}

function getPhaseProgress(phase: TrainingPhase, weekNumber: number): number {
  const phaseDuration = phase.end_week - phase.start_week + 1;
  if (weekNumber > phase.end_week) return 100;
  if (weekNumber < phase.start_week) return 0;
  return ((weekNumber - phase.start_week) / phaseDuration) * 100;
}

// --- Phase Timeline Subcomponent (#153) ---

interface PhaseTimelineProps {
  phases: TrainingPhase[];
  weekNumber: number;
}

function PhaseTimeline({ phases, weekNumber }: PhaseTimelineProps) {
  const sortedPhases = [...phases].sort((a, b) => a.start_week - b.start_week);

  return (
    <div className="space-y-1.5" aria-label="Phasen-Fortschritt">
      {/* Timeline bar */}
      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
        {sortedPhases.map((phase) => {
          const phaseDuration = phase.end_week - phase.start_week + 1;
          const colors = phaseTimelineColors[phase.phase_type] ?? phaseTimelineColors.base;
          const progress = getPhaseProgress(phase, weekNumber);

          return (
            <Popover key={phase.id}>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="relative h-full rounded-[1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)] focus-visible:ring-offset-1"
                  style={{
                    flex: phaseDuration,
                    backgroundColor: colors.empty,
                  }}
                  aria-label={`${phaseTypeLabels[phase.phase_type] ?? phase.phase_type}: ${phase.name}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div
                    className="absolute inset-y-0 left-0 rounded-[1px] transition-all duration-500 motion-reduce:transition-none"
                    style={{
                      width: `${progress}%`,
                      backgroundColor: colors.filled,
                    }}
                  />
                </button>
              </PopoverTrigger>
              <PopoverContent
                side="bottom"
                showArrow
                className="text-xs leading-relaxed"
                style={{ maxWidth: 220 }}
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
              >
                <div className="space-y-1">
                  <p className="font-medium text-[var(--color-text-base)]">{phase.name}</p>
                  <p className="text-[var(--color-text-muted)]">
                    {phaseTypeLabels[phase.phase_type] ?? phase.phase_type} · Woche{' '}
                    {phase.start_week}–{phase.end_week}
                  </p>
                  {phase.focus?.primary && phase.focus.primary.length > 0 && (
                    <p className="text-[var(--color-text-muted)]">
                      Fokus: {phase.focus.primary.join(', ')}
                    </p>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          );
        })}
      </div>

      {/* Phase labels below the bar */}
      <div className="flex gap-0.5">
        {sortedPhases.map((phase) => {
          const phaseDuration = phase.end_week - phase.start_week + 1;
          const isActive = phase.start_week <= weekNumber && weekNumber <= phase.end_week;

          return (
            <span
              key={`label-${phase.id}`}
              className={[
                'text-[10px] truncate text-center leading-tight',
                isActive
                  ? 'font-medium text-[var(--color-text-secondary)]'
                  : 'text-[var(--color-text-muted)]',
              ].join(' ')}
              style={{ flex: phaseDuration }}
            >
              {phaseDuration >= 2 ? (phaseTypeLabels[phase.phase_type] ?? phase.phase_type) : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// --- Component ---

interface PlanContextBarProps {
  planId: number;
  weekStart: string;
}

export function PlanContextBar({ planId, weekStart }: PlanContextBarProps) {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<TrainingPlan | null>(null);

  useEffect(() => {
    let cancelled = false;
    getTrainingPlan(planId)
      .then((data) => {
        if (!cancelled) setPlan(data);
      })
      .catch(() => {
        // Silently fail — bar just won't show
      });
    return () => {
      cancelled = true;
    };
  }, [planId]);

  if (!plan || plan.phases.length === 0) return null;

  const weekNumber = getWeekNumber(plan.start_date, weekStart);
  const currentPhase = getCurrentPhase(plan.phases, weekNumber);
  const totalWeeks = getTotalWeeks(plan.phases);

  if (weekNumber < 1 || weekNumber > totalWeeks) return null;

  const goal = plan.goal_summary;
  const hasTimeline = plan.phases.length > 1;

  return (
    <Card
      elevation="raised"
      padding="compact"
      className="cursor-pointer hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-150 motion-reduce:transition-none"
      onClick={() => navigate(`/settings/plans/${planId}`)}
      role="link"
      tabIndex={0}
      aria-label={`Trainingsplan: ${plan.name}`}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigate(`/settings/plans/${planId}`);
        }
      }}
    >
      <CardBody>
        <div className="space-y-2">
          {/* Header: Goal + navigation hint */}
          <div className="flex items-start gap-2 min-w-0">
            <div className="flex-1 min-w-0 space-y-0.5">
              {/* Goal line */}
              {goal && (
                <div className="flex items-center gap-1.5 min-w-0">
                  <Target className="w-3.5 h-3.5 shrink-0 text-[var(--color-text-primary)]" />
                  <span className="text-xs font-medium text-[var(--color-text-base)] truncate">
                    {goal.title}
                    {goal.target_time_formatted && (
                      <span className="text-[var(--color-text-muted)] font-normal">
                        {' '}
                        — {goal.target_time_formatted}
                      </span>
                    )}
                  </span>
                </div>
              )}

              {/* Phase description */}
              <p className="text-[11px] text-[var(--color-text-muted)]">
                {currentPhase && phaseTypeLabels[currentPhase.phase_type] && (
                  <span className="font-medium text-[var(--color-text-secondary)]">
                    {phaseTypeLabels[currentPhase.phase_type]}
                    {/* Only add separator if name is different from type label */}
                    {currentPhase.name.toLowerCase() !==
                    phaseTypeLabels[currentPhase.phase_type]?.toLowerCase()
                      ? ` · ${currentPhase.name}`
                      : ''}
                  </span>
                )}
                {currentPhase && phaseTypeLabels[currentPhase.phase_type] ? ' · ' : ''}
                Woche {weekNumber} von {totalWeeks}
              </p>
            </div>

            {/* Right side: days badge + chevron */}
            <div className="flex items-center gap-1 shrink-0">
              {goal?.days_until != null && goal.days_until >= 0 && (
                <span className="text-[10px] font-medium text-[var(--color-text-primary)] bg-[var(--color-bg-primary-subtle)] px-1.5 py-0.5 rounded-full">
                  {goal.days_until} Tage
                </span>
              )}
              <ChevronRight className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            </div>
          </div>

          {/* Phase Timeline */}
          {hasTimeline && <PhaseTimeline phases={plan.phases} weekNumber={weekNumber} />}
        </div>
      </CardBody>
    </Card>
  );
}
