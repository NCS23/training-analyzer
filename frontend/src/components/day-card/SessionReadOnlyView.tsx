import { Clock, Dumbbell, Gauge, Heart, Layers } from 'lucide-react';
import type { PlannedSession, RunDetails } from '@/api/weekly-plan';
import type { TemplateExercise } from '@/api/session-templates';
import { SegmentRow } from './SegmentRow';

interface SessionReadOnlyViewProps {
  session: PlannedSession;
  runDetails: RunDetails | null;
  templateExercises: TemplateExercise[];
}

export function SessionReadOnlyView({
  session,
  runDetails,
  templateExercises,
}: SessionReadOnlyViewProps) {
  if (session.training_type === 'strength') {
    return <StrengthView session={session} templateExercises={templateExercises} />;
  }
  if (session.training_type === 'running') {
    return <RunningView session={session} runDetails={runDetails} />;
  }
  return null;
}

function StrengthView({
  session,
  templateExercises,
}: {
  session: PlannedSession;
  templateExercises: TemplateExercise[];
}) {
  const exercises =
    session.exercises && session.exercises.length > 0
      ? session.exercises
      : templateExercises.length > 0
        ? templateExercises
        : null;

  return (
    <div className="space-y-3">
      {session.template_name && (
        <p className="text-xs text-[var(--color-text-muted)]">
          Vorlage:{' '}
          <span className="font-medium text-[var(--color-text-base)]">{session.template_name}</span>
        </p>
      )}

      {exercises && (
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
            <Dumbbell className="w-3 h-3" />
            <span>Übungen</span>
          </div>
          <div className="space-y-0.5">
            {exercises.map((ex, i) => (
              <div
                key={i}
                className="flex items-baseline justify-between text-xs px-2 py-1 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)]"
              >
                <span className="text-[var(--color-text-base)] font-medium truncate mr-2">
                  {ex.name}
                </span>
                <span className="text-[var(--color-text-muted)] whitespace-nowrap">
                  {ex.sets}×{ex.reps}
                  {ex.weight_kg != null && ` · ${ex.weight_kg}kg`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!session.exercises?.length &&
        !templateExercises.length &&
        !session.template_id &&
        !session.notes && (
          <p className="text-xs text-[var(--color-text-disabled)] italic">
            Keine Übungen oder Vorlage
          </p>
        )}

      {session.notes && (
        <p className="text-xs text-[var(--color-text-muted)] italic">{session.notes}</p>
      )}
    </div>
  );
}

// eslint-disable-next-line complexity -- Read-only Metriken-Anzeige mit vielen Fallback-Texten
function RunningView({
  session,
  runDetails: rd,
}: {
  session: PlannedSession;
  runDetails: RunDetails | null;
}) {
  const displaySegs = rd?.segments && rd.segments.length > 1 ? rd.segments : null;

  const durationText = rd?.target_duration_minutes ? `${rd.target_duration_minutes} min` : '—';
  const paceText = rd?.target_pace_min
    ? `${rd.target_pace_min}${rd.target_pace_max ? ` – ${rd.target_pace_max}` : ''} /km`
    : '—';
  const hrText =
    rd?.target_hr_min || rd?.target_hr_max
      ? `${[rd?.target_hr_min, rd?.target_hr_max].filter(Boolean).join(' – ')} bpm`
      : '—';

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
        <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
          <Clock className="w-3 h-3" />
          Dauer
        </span>
        <span className="text-[var(--color-text-base)]">{durationText}</span>

        <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
          <Gauge className="w-3 h-3" />
          Pace
        </span>
        <span className="text-[var(--color-text-base)]">{paceText}</span>

        <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
          <Heart className="w-3 h-3" />
          HF
        </span>
        <span className="text-[var(--color-text-base)]">{hrText}</span>
      </div>

      {displaySegs && (
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
            <Layers className="w-3 h-3" />
            <span>Segmente</span>
          </div>
          <div className="space-y-0.5">
            {displaySegs.map((seg, i) => (
              <SegmentRow key={i} segment={seg} />
            ))}
          </div>
        </div>
      )}

      {session.notes && (
        <p className="text-xs text-[var(--color-text-muted)] italic">{session.notes}</p>
      )}
    </div>
  );
}
