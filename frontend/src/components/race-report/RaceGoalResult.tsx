import { Card, CardBody, Badge } from '@nordlig/components';
import { Trophy, Target } from 'lucide-react';
import type { GoalComparison } from '@/api/training';

interface RaceGoalResultProps {
  goal: GoalComparison;
}

export function RaceGoalResult({ goal }: RaceGoalResultProps) {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex items-center gap-3 mb-4">
          <div
            className={`flex items-center justify-center w-12 h-12 rounded-full ${
              goal.target_achieved
                ? 'bg-[var(--color-bg-success-subtle)]'
                : 'bg-[var(--color-bg-warning-subtle)]'
            }`}
          >
            <Trophy
              className={`w-6 h-6 ${
                goal.target_achieved
                  ? 'text-[var(--color-text-success)]'
                  : 'text-[var(--color-text-warning)]'
              }`}
            />
          </div>
          <div>
            <p className="text-lg font-semibold text-[var(--color-text-base)]">{goal.goal_title}</p>
            <Badge variant={goal.target_achieved ? 'success' : 'warning'} size="xs">
              {goal.target_achieved ? 'Ziel erreicht' : 'Ziel verfehlt'}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Zielzeit</p>
            <p className="text-sm font-semibold text-[var(--color-text-base)]">
              {goal.target_time_formatted}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {goal.target_pace_formatted}/km
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Ergebnis</p>
            <p className="text-sm font-semibold text-[var(--color-text-base)]">
              {goal.actual_time_formatted}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {goal.actual_pace_formatted}/km
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Delta</p>
            <p
              className={`text-sm font-semibold ${
                goal.target_achieved
                  ? 'text-[var(--color-text-success)]'
                  : 'text-[var(--color-text-error)]'
              }`}
            >
              {goal.delta_formatted}
            </p>
            <div className="flex items-center justify-center gap-1 text-xs text-[var(--color-text-muted)]">
              <Target className="w-3 h-3" />
              <span>{goal.target_achieved ? 'schneller' : 'langsamer'}</span>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
