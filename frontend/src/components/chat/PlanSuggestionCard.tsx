import { useState } from 'react';
import { ArrowRight, Check, Loader2, Undo2 } from 'lucide-react';
import { Button } from '@nordlig/components';
import { applyPlanChange } from '@/api/chat';

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
