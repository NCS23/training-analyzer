import { Card, CardHeader, CardBody, Badge } from '@nordlig/components';
import { TrendingUp } from 'lucide-react';
import type { TrainingComparison } from '@/api/training';

interface RaceTrainingComparisonProps {
  comparison: TrainingComparison;
}

export function RaceTrainingComparison({ comparison }: RaceTrainingComparisonProps) {
  const faster = comparison.delta_pct > 0;

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-[var(--color-text-muted)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Race vs. Training</h2>
        </div>
      </CardHeader>
      <CardBody>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Training Ø</p>
            <p className="text-sm font-semibold text-[var(--color-text-base)]">
              {comparison.avg_training_pace_formatted}/km
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Race-Pace</p>
            <p className="text-sm font-semibold text-[var(--color-text-base)]">
              {comparison.race_pace_formatted}/km
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Differenz</p>
            <Badge variant={faster ? 'success' : 'warning'} size="xs">
              {faster ? '+' : ''}
              {comparison.delta_pct.toFixed(1)}%
            </Badge>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
