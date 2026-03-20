import { useState } from 'react';
import { ArrowRight, Check, Undo2 } from 'lucide-react';
import { Button } from '@nordlig/components';

export interface PlanSuggestion {
  action: 'swap' | 'skip' | 'add' | 'move' | 'replace' | 'rest_day';
  day: string;
  date?: string;
  description: string;
  reason: string;
  from?: string;
  to?: string;
}

interface PlanSuggestionCardProps {
  suggestion: PlanSuggestion;
  onApply?: (suggestion: PlanSuggestion) => void;
}

const ACTION_LABELS: Record<string, string> = {
  swap: 'Tauschen',
  skip: 'Überspringen',
  add: 'Hinzufügen',
  move: 'Verschieben',
  replace: 'Ersetzen',
  rest_day: 'Ruhetag einschieben',
};

export function PlanSuggestionCard({ suggestion, onApply }: PlanSuggestionCardProps) {
  const [applied, setApplied] = useState(false);

  const handleApply = () => {
    setApplied(true);
    onApply?.(suggestion);
  };

  const handleUndo = () => {
    setApplied(false);
    // TODO: Undo-API aufrufen wenn implementiert
  };

  return (
    <div className="my-2 rounded-[var(--radius-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--color-bg-warning-subtle)] text-[var(--color-text-warning)]">
          {ACTION_LABELS[suggestion.action] ?? suggestion.action}
        </span>
        <span className="text-xs text-[var(--color-text-muted)]">{suggestion.day}</span>
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

      <div className="flex gap-2 pt-1">
        {applied ? (
          <>
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-success)]">
              <Check className="w-3 h-3" />
              Übernommen
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleUndo}
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
            onClick={handleApply}
            className="!text-xs !px-3 !py-1 !min-h-0"
          >
            Übernehmen
          </Button>
        )}
      </div>
    </div>
  );
}
