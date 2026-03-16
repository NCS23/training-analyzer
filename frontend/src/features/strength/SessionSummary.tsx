import { Card, CardBody } from '@nordlig/components';
import { Dumbbell, Layers, Weight, Clock, Repeat, Timer, MapPin } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { ExerciseInput } from '@/api/strength';
import { useTonnageCalc } from '@/hooks/useTonnageCalc';

interface SessionSummaryProps {
  exercises: ExerciseInput[];
  durationMinutes: number;
}

function formatDuration(totalSec: number): { value: string; unit: string } {
  if (totalSec >= 3600) {
    return { value: (totalSec / 3600).toFixed(1), unit: 'h' };
  }
  if (totalSec >= 60) {
    return { value: String(Math.round(totalSec / 60)), unit: 'min' };
  }
  return { value: String(totalSec), unit: 's' };
}

function formatDistance(meters: number): { value: string; unit: string } {
  if (meters >= 1000) {
    return { value: (meters / 1000).toFixed(1), unit: 'km' };
  }
  return { value: String(Math.round(meters)), unit: 'm' };
}

export function SessionSummary({ exercises, durationMinutes }: SessionSummaryProps) {
  const { total, totalReps, totalDuration, totalDistance, setCount, exerciseCount } =
    useTonnageCalc(exercises);

  const tiles: { label: string; value: string; unit: string; icon: LucideIcon }[] = [
    { label: 'Übungen', value: String(exerciseCount), unit: '', icon: Dumbbell },
    { label: 'Sätze', value: String(setCount), unit: '', icon: Layers },
    { label: 'Dauer', value: String(durationMinutes), unit: 'min', icon: Clock },
  ];

  // Only show tonnage if there are weighted exercises
  if (total > 0) {
    tiles.push({
      label: 'Tonnage',
      value: total >= 1000 ? (total / 1000).toFixed(1) : String(total),
      unit: total >= 1000 ? 't' : 'kg',
      icon: Weight,
    });
  }

  // Only show total reps if there are rep-based exercises
  if (totalReps > 0) {
    tiles.push({ label: 'Wdh.', value: String(totalReps), unit: '', icon: Repeat });
  }

  // Only show TUT if there are duration-based exercises
  if (totalDuration > 0) {
    const fmt = formatDuration(totalDuration);
    tiles.push({ label: 'TUT', value: fmt.value, unit: fmt.unit, icon: Timer });
  }

  // Only show distance if there are distance-based exercises
  if (totalDistance > 0) {
    const fmt = formatDistance(totalDistance);
    tiles.push({ label: 'Distanz', value: fmt.value, unit: fmt.unit, icon: MapPin });
  }

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
