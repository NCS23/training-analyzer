import { useState } from 'react';
import { ArrowRight, Check, Loader2, Undo2 } from 'lucide-react';
import { Button } from '@nordlig/components';
import { applyPlanChange, type PlanInterval, type PlanRunDetails } from '@/api/chat';

export interface PlanSuggestion {
  action: 'swap' | 'skip' | 'add' | 'move' | 'replace' | 'rest_day';
  day: string;
  date?: string;
  week_start?: string;
  plan_id?: number;
  description: string;
  reason: string;
  from?: string;
  to?: string;
  training_type?: 'running' | 'strength';
  run_details?: PlanRunDetails;
}

interface PlanSuggestionCardProps {
  suggestion: PlanSuggestion;
  onApplied?: () => void;
}

const ACTION_LABELS: Record<string, string> = {
  swap: 'Tauschen',
  skip: 'Überspringen',
  add: 'Hinzufügen',
  move: 'Verschieben',
  replace: 'Ersetzen',
  rest_day: 'Ruhetag einschieben',
};

const SEGMENT_LABELS: Record<string, string> = {
  warmup: 'Warmup',
  cooldown: 'Cooldown',
  steady: 'Steady',
  work: 'Belastung',
  recovery_jog: 'Trab-Pause',
  rest: 'Pause',
  strides: 'Steigerungen',
  drills: 'Lauf-ABC',
};

function formatPaceRange(min?: string, max?: string): string | null {
  if (min && max) return `${min}–${max}/km`;
  if (min) return `${min}/km`;
  if (max) return `${max}/km`;
  return null;
}

function formatDuration(interval: PlanInterval): string | null {
  if (interval.duration_minutes) {
    const total = interval.duration_minutes;
    return total >= 1
      ? `${total % 1 === 0 ? total : total.toFixed(1)} min`
      : `${Math.round(total * 60)} s`;
  }
  if (interval.distance_km) return `${interval.distance_km} km`;
  return null;
}

function RunDetailsPreview({ details }: { details: PlanRunDetails }) {
  const intervals = details.intervals ?? [];
  const totalDuration = details.target_duration_minutes;
  const overallPace = formatPaceRange(details.target_pace_min, details.target_pace_max);

  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--color-border-subtle)] bg-[var(--color-bg-subtle)] p-2 space-y-1">
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <span className="font-medium text-[var(--color-text-base)]">{details.run_type}</span>
        {totalDuration && <span>· {totalDuration} min gesamt</span>}
        {overallPace && <span>· {overallPace}</span>}
      </div>
      {intervals.length > 0 && (
        <ol className="space-y-1">
          {intervals.map((interval, idx) => {
            const label = SEGMENT_LABELS[interval.type] ?? interval.type;
            const dur = formatDuration(interval);
            const pace = formatPaceRange(interval.target_pace_min, interval.target_pace_max);
            const repeats = interval.repeats && interval.repeats > 1 ? `${interval.repeats}× ` : '';
            return (
              <li
                key={idx}
                className="flex items-baseline gap-2 text-xs text-[var(--color-text-base)]"
              >
                <span className="font-medium min-w-[5.5rem]">
                  {repeats}
                  {label}
                </span>
                {dur && <span className="text-[var(--color-text-muted)]">{dur}</span>}
                {pace && <span className="text-[var(--color-text-muted)]">@ {pace}</span>}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

export function PlanSuggestionCard({ suggestion, onApplied }: PlanSuggestionCardProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'applied' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApply = async () => {
    if (!suggestion.date) {
      setStatus('error');
      setErrorMsg('Kein Datum angegeben — Änderung kann nicht angewendet werden.');
      return;
    }

    setStatus('loading');
    setErrorMsg(null);

    try {
      await applyPlanChange({
        action: suggestion.action,
        date: suggestion.date,
        week_start: suggestion.week_start,
        plan_id: suggestion.plan_id,
        description: suggestion.description,
        reason: suggestion.reason,
        from: suggestion.from,
        to: suggestion.to,
        training_type: suggestion.training_type,
        run_details: suggestion.run_details,
      });
      setStatus('applied');
      onApplied?.();
    } catch {
      setStatus('error');
      setErrorMsg('Änderung konnte nicht angewendet werden.');
    }
  };

  const handleUndo = async () => {
    // Undo ist über den bestehenden Undo-Mechanismus im Wochenplan möglich
    // Hier setzen wir nur den Status zurück
    setStatus('idle');
    setErrorMsg(null);
  };

  return (
    <div className="my-2 rounded-[var(--radius-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--color-bg-warning-subtle)] text-[var(--color-text-warning)]">
          {ACTION_LABELS[suggestion.action] ?? suggestion.action}
        </span>
        <span className="text-xs text-[var(--color-text-muted)]">{suggestion.day}</span>
        {suggestion.date && (
          <span className="text-xs text-[var(--color-text-muted)]">({suggestion.date})</span>
        )}
      </div>

      <p className="text-sm text-[var(--color-text-base)]">{suggestion.description}</p>

      {suggestion.run_details && <RunDetailsPreview details={suggestion.run_details} />}

      {suggestion.from && suggestion.to && (
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <span className="line-through">{suggestion.from}</span>
          <ArrowRight className="w-3 h-3" />
          <span className="font-medium text-[var(--color-text-base)]">{suggestion.to}</span>
        </div>
      )}

      <p className="text-xs text-[var(--color-text-muted)] italic">{suggestion.reason}</p>

      {errorMsg && <p className="text-xs text-[var(--color-text-error)]">{errorMsg}</p>}

      <div className="flex gap-2 pt-1">
        {status === 'applied' ? (
          <>
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-success)]">
              <Check className="w-3 h-3" />
              Übernommen
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void handleUndo()}
              className="!text-xs !px-2 !py-1 !min-h-0"
            >
              <Undo2 className="w-3 h-3 mr-1" />
              Rückgängig
            </Button>
          </>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={() => void handleApply()}
            disabled={status === 'loading'}
            className="!text-xs !px-3 !py-1 !min-h-0"
          >
            {status === 'loading' ? (
              <Loader2 className="w-3 h-3 mr-1 animate-spin motion-reduce:animate-none" />
            ) : null}
            Übernehmen
          </Button>
        )}
      </div>
    </div>
  );
}
