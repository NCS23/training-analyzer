import type { LucideIcon } from 'lucide-react';
import {
  Clock,
  MapPin,
  Timer,
  Heart,
  HeartPulse,
  Footprints,
  Dumbbell,
  Layers,
  Weight,
  TrendingUp,
  Gauge,
} from 'lucide-react';
import { Card, CardBody } from '@nordlig/components';
import type { SessionDetail } from '@/api/training';

type MetricItem = {
  label: string;
  value: string;
  unit: string;
  icon: LucideIcon;
  kind?: 'rpe' | 'combined-hr';
  rpeValue?: number;
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

// eslint-disable-next-line complexity -- metric collection with many conditional fields
function buildMetrics(
  session: SessionDetail,
  sessionGap: string | null,
  effectiveRpe: number | null,
): MetricItem[] {
  const metrics: MetricItem[] = [];

  if (session.duration_sec != null)
    metrics.push({
      label: 'Dauer',
      value: formatDuration(session.duration_sec),
      unit: '',
      icon: Clock,
    });
  if (session.distance_km != null)
    metrics.push({
      label: 'Distanz',
      value: String(session.distance_km),
      unit: 'km',
      icon: MapPin,
    });
  if (session.pace) metrics.push({ label: 'Pace', value: session.pace, unit: '/km', icon: Timer });
  if (sessionGap) metrics.push({ label: 'GAP', value: sessionGap, unit: '/km', icon: TrendingUp });
  if (session.hr_avg != null)
    metrics.push({ label: 'Ø HF', value: String(session.hr_avg), unit: 'bpm', icon: Heart });

  if (session.hr_max != null && session.hr_min != null)
    metrics.push({
      label: 'Max / Min HF',
      value: `${session.hr_max}`,
      unit: `/ ${session.hr_min} bpm`,
      icon: HeartPulse,
      kind: 'combined-hr',
    });
  else if (session.hr_max != null)
    metrics.push({ label: 'Max HF', value: String(session.hr_max), unit: 'bpm', icon: HeartPulse });
  else if (session.hr_min != null)
    metrics.push({ label: 'Min HF', value: String(session.hr_min), unit: 'bpm', icon: HeartPulse });

  if (session.cadence_avg != null)
    metrics.push({
      label: 'Ø Kadenz',
      value: String(session.cadence_avg),
      unit: 'spm',
      icon: Footprints,
    });

  if (session.exercises && session.exercises.length > 0) {
    metrics.push({
      label: 'Übungen',
      value: String(session.exercises.length),
      unit: '',
      icon: Dumbbell,
    });
    const totalSets = session.exercises.reduce(
      (sum: number, ex: { sets: unknown[] }) => sum + ex.sets.length,
      0,
    );
    metrics.push({ label: 'Sätze', value: String(totalSets), unit: '', icon: Layers });
    let tonnage = 0;
    for (const ex of session.exercises) {
      for (const s of (ex as { sets: Array<{ reps: number; weight_kg: number; status: string }> })
        .sets) {
        if (s.status !== 'skipped') tonnage += s.reps * s.weight_kg;
      }
    }
    if (tonnage > 0)
      metrics.push({
        label: 'Tonnage',
        value: tonnage >= 1000 ? `${(tonnage / 1000).toFixed(1)}` : String(Math.round(tonnage)),
        unit: tonnage >= 1000 ? 't' : 'kg',
        icon: Weight,
      });
  }

  if (effectiveRpe != null)
    metrics.push({
      label: 'RPE',
      value: String(effectiveRpe),
      unit: '/10',
      icon: Gauge,
      kind: 'rpe',
      rpeValue: effectiveRpe,
    });

  return metrics;
}

interface SessionMetricsGridProps {
  session: SessionDetail;
  sessionGap: string | null;
  effectiveRpe: number | null;
}

export function SessionMetricsGrid({ session, sessionGap, effectiveRpe }: SessionMetricsGridProps) {
  const metrics = buildMetrics(session, sessionGap, effectiveRpe);

  return (
    <section aria-label="Kennzahlen">
      <Card elevation="raised">
        <CardBody>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-[10px]">
            {metrics.map((m) => (
              <div
                key={m.label}
                className={`rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3 ${
                  m.kind === 'rpe' ? 'flex flex-col justify-center' : ''
                }`}
              >
                <div className="flex items-center gap-1 mb-1 sm:mb-2">
                  <m.icon
                    className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]"
                    aria-hidden="true"
                  />
                  <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                    {m.label}
                  </p>
                </div>
                {m.kind === 'rpe' ? (
                  <div className="flex items-center gap-2 sm:gap-[10px]">
                    <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none shrink-0">
                      {m.value}
                      <span className="text-[11px] sm:text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
                        {m.unit}
                      </span>
                    </p>
                    <div className="flex-1 h-1 rounded-full bg-[var(--color-border-default)] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[var(--color-interactive-primary)] transition-all duration-500 motion-reduce:transition-none"
                        style={{ width: `${(m.rpeValue ?? 0) * 10}%` }}
                      />
                    </div>
                  </div>
                ) : m.kind === 'combined-hr' ? (
                  <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                    {m.value}
                    <span className="text-[11px] sm:text-[14px] font-normal text-[var(--color-text-muted)]">
                      {' '}
                      {m.unit}
                    </span>
                  </p>
                ) : (
                  <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                    {m.value}
                    {m.unit && (
                      <span className="text-[11px] sm:text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
                        {' '}
                        {m.unit}
                      </span>
                    )}
                  </p>
                )}
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </section>
  );
}
