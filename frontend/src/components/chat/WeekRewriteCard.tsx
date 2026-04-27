import { useState } from 'react';
import { CalendarRange, Check, Loader2 } from 'lucide-react';
import { Button } from '@nordlig/components';
import { applyRecommendations } from '@/api/weekly-plan';

export interface WeekRewriteSuggestion {
  review_week_start: string;
  target_week_start?: string;
  plan_id?: number;
  summary: string;
  reason: string;
  recommendations: string[];
}

interface WeekRewriteCardProps {
  suggestion: WeekRewriteSuggestion;
  onApplied?: () => void;
}

export function WeekRewriteCard({ suggestion, onApplied }: WeekRewriteCardProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'applied' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [appliedCount, setAppliedCount] = useState<number | null>(null);

  const handleApply = async () => {
    if (!suggestion.review_week_start) {
      setStatus('error');
      setErrorMsg('Keine Review-Woche angegeben — Änderung kann nicht angewendet werden.');
      return;
    }
    if (!suggestion.recommendations || suggestion.recommendations.length === 0) {
      setStatus('error');
      setErrorMsg('Keine Empfehlungen — nichts anzuwenden.');
      return;
    }

    setStatus('loading');
    setErrorMsg(null);

    try {
      const result = await applyRecommendations({
        week_start: suggestion.review_week_start,
        recommendations: suggestion.recommendations,
      });
      setAppliedCount(result.applied_count);
      setStatus('applied');
      onApplied?.();
    } catch {
      setStatus('error');
      setErrorMsg('Wochen-Umstrukturierung konnte nicht angewendet werden.');
    }
  };

  return (
    <div className="my-2 rounded-[var(--radius-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)]">
          <CalendarRange className="w-3 h-3" />
          Wochen-Umstrukturierung
        </span>
        {suggestion.target_week_start && (
          <span className="text-xs text-[var(--color-text-muted)]">
            ab {suggestion.target_week_start}
          </span>
        )}
      </div>

      <p className="text-sm text-[var(--color-text-base)]">{suggestion.summary}</p>

      {suggestion.recommendations.length > 0 && (
        <ul className="list-disc list-inside space-y-0.5 text-xs text-[var(--color-text-base)]">
          {suggestion.recommendations.map((rec, idx) => (
            <li key={idx}>{rec}</li>
          ))}
        </ul>
      )}

      <p className="text-xs text-[var(--color-text-muted)] italic">{suggestion.reason}</p>

      {errorMsg && <p className="text-xs text-[var(--color-text-error)]">{errorMsg}</p>}

      <div className="flex gap-2 pt-1">
        {status === 'applied' ? (
          <div className="flex items-center gap-1 text-xs text-[var(--color-text-success)]">
            <Check className="w-3 h-3" />
            Übernommen
            {appliedCount !== null && <span>({appliedCount} Sessions)</span>}
          </div>
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
