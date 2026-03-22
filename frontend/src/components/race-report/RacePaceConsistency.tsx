import { Card, CardHeader, CardBody, Badge } from '@nordlig/components';
import { Gauge } from 'lucide-react';
import type { PaceConsistency } from '@/api/training';

interface RacePaceConsistencyProps {
  consistency: PaceConsistency;
}

const CONSISTENCY_VARIANT: Record<string, 'success' | 'warning' | 'neutral'> = {
  'Sehr gleichmaessig': 'success',
  Gleichmaessig: 'neutral',
  Ungleichmaessig: 'warning',
};

export function RacePaceConsistency({ consistency }: RacePaceConsistencyProps) {
  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Gauge className="w-4 h-4 text-[var(--color-text-muted)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Pace-Konsistenz</h2>
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex items-baseline gap-3 mb-3">
          <span className="text-2xl font-bold text-[var(--color-text-base)]">
            {consistency.coefficient_of_variation}%
          </span>
          <Badge variant={CONSISTENCY_VARIANT[consistency.label] ?? 'neutral'} size="xs">
            {consistency.label}
          </Badge>
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-2 rounded-[var(--radius-sm)] bg-[var(--color-bg-success-subtle)]">
            <p className="text-[var(--color-text-muted)]">Schnellster Km</p>
            <p className="font-semibold text-[var(--color-text-success)]">
              Km {consistency.fastest_km} — {consistency.fastest_pace_formatted}/km
            </p>
          </div>
          <div className="p-2 rounded-[var(--radius-sm)] bg-[var(--color-bg-warning-subtle)]">
            <p className="text-[var(--color-text-muted)]">Langsamster Km</p>
            <p className="font-semibold text-[var(--color-text-warning)]">
              Km {consistency.slowest_km} — {consistency.slowest_pace_formatted}/km
            </p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
