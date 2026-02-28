import { useMemo } from 'react';
import { Card, CardBody } from '@nordlig/components';
import { Dumbbell, Layers, Weight, Clock } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { ExerciseInput } from '@/api/strength';

interface SessionSummaryProps {
  exercises: ExerciseInput[];
  durationMinutes: number;
}

export function SessionSummary({ exercises, durationMinutes }: SessionSummaryProps) {
  const metrics = useMemo(() => {
    let totalSets = 0;
    let tonnage = 0;

    for (const ex of exercises) {
      for (const s of ex.sets) {
        totalSets++;
        if (s.status !== 'skipped') {
          tonnage += s.reps * s.weight_kg;
        }
      }
    }

    return {
      exercises: exercises.length,
      sets: totalSets,
      tonnage: Math.round(tonnage * 10) / 10,
      duration: durationMinutes,
    };
  }, [exercises, durationMinutes]);

  const tiles: { label: string; value: string; unit: string; icon: LucideIcon }[] = [
    { label: 'Übungen', value: String(metrics.exercises), unit: '', icon: Dumbbell },
    { label: 'Sätze', value: String(metrics.sets), unit: '', icon: Layers },
    {
      label: 'Tonnage',
      value:
        metrics.tonnage >= 1000
          ? (metrics.tonnage / 1000).toFixed(1)
          : String(metrics.tonnage),
      unit: metrics.tonnage >= 1000 ? 't' : 'kg',
      icon: Weight,
    },
    { label: 'Dauer', value: String(metrics.duration), unit: 'min', icon: Clock },
  ];

  return (
    <section aria-label="Kennzahlen" aria-live="polite">
      <Card elevation="raised">
        <CardBody>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {tiles.map((m) => (
              <div
                key={m.label}
                className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <m.icon
                    className="w-3.5 h-3.5 text-[var(--color-text-muted)]"
                    aria-hidden="true"
                  />
                  <p className="text-xs text-[var(--color-text-muted)]">{m.label}</p>
                </div>
                <p className="text-xl font-semibold text-[var(--color-text-base)] tabular-nums">
                  {m.value}
                  {m.unit && (
                    <span className="text-sm font-normal text-[var(--color-text-muted)] ml-1">
                      {m.unit}
                    </span>
                  )}
                </p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </section>
  );
}
