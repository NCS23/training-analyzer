/**
 * Read-only view of running details in a session template.
 */
import { Card, CardBody, Badge } from '@nordlig/components';
import type { RunDetails } from '@/api/weekly-plan';
import { trainingTypeOptions } from '@/constants/training';

const RUN_TYPE_OPTIONS = trainingTypeOptions.map((opt) => ({
  value: opt.value,
  label: opt.label,
}));

const SEGMENT_TYPE_LABELS: Record<string, string> = {
  warmup: 'Einlaufen',
  cooldown: 'Auslaufen',
  steady: 'Steady',
  work: 'Belastung',
  recovery_jog: 'Trab-Pause',
  rest: 'Pause',
  strides: 'Steigerungen',
  drills: 'Lauf-ABC',
};

interface RunningReadViewProps {
  runType: string;
  runDetails: RunDetails | null;
}

// eslint-disable-next-line complexity -- read-only view with many display conditions
export function RunningReadView({ runType, runDetails }: RunningReadViewProps) {
  return (
    <Card elevation="raised" padding="spacious">
      <CardBody>
        <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">Lauf-Details</h2>
        <div className="space-y-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="neutral" size="sm">
                {RUN_TYPE_OPTIONS.find((o) => o.value === runType)?.label ?? runType}
              </Badge>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-2 gap-x-4 mt-2">
              {runDetails?.target_duration_minutes != null && (
                <div>
                  <span className="block text-xs text-[var(--color-text-muted)]">Dauer</span>
                  <p className="text-sm text-[var(--color-text-base)]">
                    {runDetails.target_duration_minutes} min
                  </p>
                </div>
              )}
              {(runDetails?.target_pace_min || runDetails?.target_pace_max) && (
                <div>
                  <span className="block text-xs text-[var(--color-text-muted)]">Pace</span>
                  <p className="text-sm text-[var(--color-text-base)]">
                    {runDetails.target_pace_min ?? '?'} – {runDetails.target_pace_max ?? '?'} min/km
                  </p>
                </div>
              )}
              {(runDetails?.target_hr_min != null || runDetails?.target_hr_max != null) && (
                <div>
                  <span className="block text-xs text-[var(--color-text-muted)]">Herzfrequenz</span>
                  <p className="text-sm text-[var(--color-text-base)]">
                    {runDetails?.target_hr_min ?? '?'} – {runDetails?.target_hr_max ?? '?'} bpm
                  </p>
                </div>
              )}
            </div>
          </div>

          {runDetails?.intervals && runDetails.intervals.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-[var(--color-text-base)] mb-2">
                Segmente ({runDetails.intervals.length})
              </h3>
              <div className="space-y-1">
                {runDetails.intervals.map((interval, iIdx) => (
                  <div
                    key={iIdx}
                    className="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)]"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-medium text-[var(--color-text-base)]">
                        {SEGMENT_TYPE_LABELS[interval.type] ?? interval.type}
                      </span>
                      {interval.repeats > 1 && (
                        <span className="text-xs text-[var(--color-text-muted)]">
                          ×{interval.repeats}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)] shrink-0 ml-2">
                      {interval.duration_minutes != null && (
                        <span>{interval.duration_minutes} min</span>
                      )}
                      {interval.distance_km != null && <span>{interval.distance_km} km</span>}
                      {(interval.target_pace_min || interval.target_pace_max) && (
                        <span>
                          {interval.target_pace_min ?? '?'}–{interval.target_pace_max ?? '?'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
