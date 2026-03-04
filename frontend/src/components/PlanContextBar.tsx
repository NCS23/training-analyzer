import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target } from 'lucide-react';
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

// --- Helpers ---

function getWeekNumber(planStartDate: string, weekStart: string): number {
  const planStart = new Date(planStartDate);
  // Ensure plan start is a Monday
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

  // Don't show if week is outside plan range
  if (weekNumber < 1 || weekNumber > totalWeeks) return null;

  const goal = plan.goal_summary;
  const phaseLabel = currentPhase
    ? `${currentPhase.name} · Woche ${weekNumber} von ${totalWeeks}`
    : `Woche ${weekNumber} von ${totalWeeks}`;

  return (
    <button
      type="button"
      onClick={() => navigate(`/settings/plans/${planId}`)}
      className={[
        'w-full text-left px-3 py-2.5',
        'rounded-[var(--radius-container-sm)]',
        'bg-[var(--color-bg-surface)] border border-[var(--color-border-muted)]',
        'hover:bg-[var(--color-bg-surface-hover)]',
        'transition-colors duration-150 motion-reduce:transition-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
      ].join(' ')}
      aria-label={`Trainingsplan: ${plan.name}`}
    >
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
          {goal.days_until != null && goal.days_until >= 0 && (
            <span className="ml-auto shrink-0 text-[10px] font-medium text-[var(--color-text-primary)] bg-[var(--color-bg-primary-subtle)] px-1.5 py-0.5 rounded-full">
              {goal.days_until} Tage
            </span>
          )}
        </div>
      )}

      {/* Phase line */}
      <p className={['text-[11px] text-[var(--color-text-muted)]', goal ? 'mt-0.5' : ''].join(' ')}>
        {currentPhase && phaseTypeLabels[currentPhase.phase_type] && (
          <span className="font-medium text-[var(--color-text-secondary)]">
            {phaseTypeLabels[currentPhase.phase_type]}
          </span>
        )}
        {currentPhase && phaseTypeLabels[currentPhase.phase_type] ? ' · ' : ''}
        {phaseLabel}
      </p>
    </button>
  );
}
