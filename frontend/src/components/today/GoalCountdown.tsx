import { Card, CardBody } from '@nordlig/components';
import { Target, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { GoalSummary } from '@/api/fitness';

interface Props {
  goal: GoalSummary;
}

export function GoalCountdown({ goal }: Props) {
  return (
    <section aria-label="Wettkampf-Ziel">
      <Link to="/plan" className="block">
        <Card elevation="raised">
          <CardBody>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-10 w-10 shrink-0 rounded-full bg-[var(--color-bg-warning-subtle)]">
                <Target className="h-5 w-5 text-[var(--color-text-warning)]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--color-text-base)]">{goal.title}</p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Noch {goal.days_until} Tage
                  {goal.target_time_formatted && ` · Ziel: ${goal.target_time_formatted}`}
                </p>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-[var(--color-text-muted)]" />
            </div>
          </CardBody>
        </Card>
      </Link>
    </section>
  );
}
