import { Popover, PopoverTrigger, PopoverContent } from '@nordlig/components';
import type { TrainingPhase } from '@/api/training-plans';
import { phaseTypeLabels } from './plan-helpers';

// --- Phase Timeline Colors ---

const phaseTimelineColors: Record<string, { filled: string; empty: string }> = {
  base: { filled: 'var(--color-text-muted)', empty: 'var(--color-border-muted)' },
  build: { filled: 'var(--color-interactive-primary)', empty: 'var(--color-bg-primary-subtle)' },
  peak: { filled: 'var(--color-text-primary)', empty: 'var(--color-bg-primary-muted)' },
  taper: { filled: 'var(--color-text-accent)', empty: 'var(--color-bg-accent-subtle)' },
  transition: { filled: 'var(--color-text-muted)', empty: 'var(--color-border-muted)' },
};

// --- Helpers ---

function getPhaseProgress(phase: TrainingPhase, weekNumber: number): number {
  const phaseDuration = phase.end_week - phase.start_week + 1;
  if (weekNumber > phase.end_week) return 100;
  if (weekNumber < phase.start_week) return 0;
  return ((weekNumber - phase.start_week) / phaseDuration) * 100;
}

// --- PhaseTimeline Component ---

interface PhaseTimelineProps {
  phases: TrainingPhase[];
  weekNumber: number;
}

export function PhaseTimeline({ phases, weekNumber }: PhaseTimelineProps) {
  const sortedPhases = [...phases].sort((a, b) => a.start_week - b.start_week);

  return (
    <div className="space-y-1.5" aria-label="Phasen-Fortschritt">
      {/* Timeline bar */}
      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
        {sortedPhases.map((phase) => {
          const phaseDuration = phase.end_week - phase.start_week + 1;
          const colors = phaseTimelineColors[phase.phase_type] ?? phaseTimelineColors.base;
          const progress = getPhaseProgress(phase, weekNumber);

          return (
            <Popover key={phase.id}>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="relative h-full rounded-[1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)] focus-visible:ring-offset-1"
                  style={{
                    flex: phaseDuration,
                    backgroundColor: colors.empty,
                  }}
                  aria-label={`${phaseTypeLabels[phase.phase_type] ?? phase.phase_type}: ${phase.name}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div
                    className="absolute inset-y-0 left-0 rounded-[1px] transition-all duration-500 motion-reduce:transition-none"
                    style={{
                      width: `${progress}%`,
                      backgroundColor: colors.filled,
                    }}
                  />
                </button>
              </PopoverTrigger>
              <PopoverContent
                side="bottom"
                showArrow
                className="text-xs leading-relaxed"
                style={{ maxWidth: 220 }}
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
              >
                <div className="space-y-1">
                  <p className="font-medium text-[var(--color-text-base)]">{phase.name}</p>
                  <p className="text-[var(--color-text-muted)]">
                    {phaseTypeLabels[phase.phase_type] ?? phase.phase_type} · Woche{' '}
                    {phase.start_week}–{phase.end_week}
                  </p>
                  {phase.focus?.primary && phase.focus.primary.length > 0 && (
                    <p className="text-[var(--color-text-muted)]">
                      Fokus: {phase.focus.primary.join(', ')}
                    </p>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          );
        })}
      </div>

      {/* Phase labels below the bar */}
      <div className="flex gap-0.5">
        {sortedPhases.map((phase) => {
          const phaseDuration = phase.end_week - phase.start_week + 1;
          const isActive = phase.start_week <= weekNumber && weekNumber <= phase.end_week;

          return (
            <span
              key={`label-${phase.id}`}
              className={[
                'text-[10px] truncate text-center leading-tight',
                isActive
                  ? 'font-medium text-[var(--color-text-secondary)]'
                  : 'text-[var(--color-text-muted)]',
              ].join(' ')}
              style={{ flex: phaseDuration }}
            >
              {phaseDuration >= 2 ? (phaseTypeLabels[phase.phase_type] ?? phase.phase_type) : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
}
