import { AlertCircle, AlertTriangle, CheckCircle, Dumbbell } from 'lucide-react';
import { Select } from '@nordlig/components';
import type { YamlValidationResult, YamlValidationIssue } from '@/api/training-plans';

interface Props {
  result: YamlValidationResult;
  filename: string;
  exerciseReplacements?: Record<string, string>;
  onExerciseReplacementChange?: (original: string, replacement: string) => void;
}

/** Value for the "create new" option in the exercise Select. */
const CREATE_NEW = '__create_new__';

export function YamlValidationResultPanel({
  result,
  filename,
  exerciseReplacements,
  onExerciseReplacementChange,
}: Props) {
  const hasErrors = result.errors.length > 0;
  const hasUnknownExercises = result.unknown_exercises.length > 0;
  // Filter out unknown_exercise warnings from the generic list to avoid duplication
  const genericWarnings = result.warnings.filter(
    (w: YamlValidationIssue) => w.code !== 'unknown_exercise_name',
  );
  const hasGenericWarnings = genericWarnings.length > 0;
  const hasAnyWarning = hasGenericWarnings || hasUnknownExercises;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {hasErrors ? (
          <AlertCircle className="w-5 h-5 text-[var(--color-text-error)] shrink-0" />
        ) : hasAnyWarning ? (
          <AlertTriangle className="w-5 h-5 text-[var(--color-text-warning)] shrink-0" />
        ) : (
          <CheckCircle className="w-5 h-5 text-[var(--color-text-success)] shrink-0" />
        )}
        <div>
          <p className="text-sm font-medium text-[var(--color-text-base)]">{filename}</p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {hasErrors
              ? `${result.errors.length} Fehler gefunden — Import nicht moeglich.`
              : hasAnyWarning
                ? 'Hinweise vorhanden — Import trotzdem moeglich.'
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

      {hasGenericWarnings && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-[var(--color-text-warning)]">Hinweise</p>
          {genericWarnings.map((issue, i) => (
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

      {hasUnknownExercises && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-[var(--color-text-warning)]">
            Unbekannte Uebungen
          </p>
          {result.unknown_exercises.map((ex) => {
            const selectedValue = exerciseReplacements?.[ex.exercise_name] ?? CREATE_NEW;
            const options = [
              ...ex.suggestions.map((s) => ({ value: s, label: s })),
              { value: CREATE_NEW, label: 'Neu erstellen' },
            ];

            return (
              <div
                key={ex.exercise_name}
                className="flex flex-col gap-2 bg-[var(--color-bg-warning-subtle)] rounded-[var(--radius-component-sm)] px-3 py-2.5"
              >
                <div className="flex items-start gap-2">
                  <Dumbbell className="w-3.5 h-3.5 text-[var(--color-text-warning)] shrink-0 mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-[var(--color-text-base)]">
                      <span className="font-medium">&bdquo;{ex.exercise_name}&ldquo;</span> nicht
                      in der Bibliothek
                    </p>
                    <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">
                      {ex.locations.length === 1
                        ? `Feld: ${ex.locations[0]}`
                        : `${ex.locations.length} Verwendungen`}
                    </p>
                  </div>
                </div>
                {onExerciseReplacementChange && (
                  <Select
                    inputSize="sm"
                    value={selectedValue}
                    options={options}
                    onChange={(val) => {
                      onExerciseReplacementChange(
                        ex.exercise_name,
                        val === CREATE_NEW ? '' : (val ?? ''),
                      );
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
