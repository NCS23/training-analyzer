import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';
import type { YamlValidationResult } from '@/api/training-plans';

interface Props {
  result: YamlValidationResult;
  filename: string;
}

export function YamlValidationResultPanel({ result, filename }: Props) {
  const hasErrors = result.errors.length > 0;
  const hasWarnings = result.warnings.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {hasErrors ? (
          <AlertCircle className="w-5 h-5 text-[var(--color-text-error)] shrink-0" />
        ) : hasWarnings ? (
          <AlertTriangle className="w-5 h-5 text-[var(--color-text-warning)] shrink-0" />
        ) : (
          <CheckCircle className="w-5 h-5 text-[var(--color-text-success)] shrink-0" />
        )}
        <div>
          <p className="text-sm font-medium text-[var(--color-text-base)]">{filename}</p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {hasErrors
              ? `${result.errors.length} Fehler gefunden — Import nicht moeglich.`
              : hasWarnings
                ? `${result.warnings.length} Hinweis${result.warnings.length > 1 ? 'e' : ''} — Import trotzdem moeglich.`
                : 'Keine Probleme gefunden.'}
          </p>
        </div>
      </div>

      {hasErrors && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-[var(--color-text-error)]">Fehler</p>
          {result.errors.map((issue, i) => (
            <div
              key={`err-${i}`}
              className="flex items-start gap-2 text-xs bg-[var(--color-bg-error-subtle)] rounded-[var(--radius-component-sm)] px-3 py-2"
            >
              <AlertCircle className="w-3.5 h-3.5 text-[var(--color-text-error)] shrink-0 mt-0.5" />
              <div>
                <p className="text-[var(--color-text-base)]">{issue.message}</p>
                {issue.location && (
                  <p className="text-[var(--color-text-muted)] mt-0.5">Feld: {issue.location}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {hasWarnings && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-[var(--color-text-warning)]">Hinweise</p>
          {result.warnings.map((issue, i) => (
            <div
              key={`warn-${i}`}
              className="flex items-start gap-2 text-xs bg-[var(--color-bg-warning-subtle)] rounded-[var(--radius-component-sm)] px-3 py-2"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-[var(--color-text-warning)] shrink-0 mt-0.5" />
              <div>
                <p className="text-[var(--color-text-base)]">{issue.message}</p>
                {issue.location && (
                  <p className="text-[var(--color-text-muted)] mt-0.5">Feld: {issue.location}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
