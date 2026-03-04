import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Target } from 'lucide-react';
import { Card, CardBody } from '@nordlig/components';
import { getTrainingPlan } from '@/api/training-plans';
import type { TrainingPlan } from '@/api/training-plans';
import { PhaseTimeline } from './PhaseTimeline';
import { phaseTypeLabels, getWeekNumber, getCurrentPhase, getTotalWeeks } from './plan-helpers';

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
      onClick={() => navigate(`/plan/programs/${planId}`)}
      role="link"
      tabIndex={0}
      aria-label={`Trainingsplan: ${plan.name}`}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigate(`/plan/programs/${planId}`);
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
