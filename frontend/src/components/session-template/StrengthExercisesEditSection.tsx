/**
 * Editable strength exercises list for session templates.
 */
import { Button, Card, CardBody, Input, NumberInput, Label, Badge } from '@nordlig/components';
import { Dumbbell, Plus, Trash2, ChevronDown, ChevronUp, GripVertical } from 'lucide-react';
import { categoryBadgeVariant } from '@/constants/training';
import { CATEGORY_OPTIONS, CATEGORY_LABELS, EXERCISE_TYPE_OPTIONS } from '@/utils/exercise-helpers';
import type { ExerciseForm } from '@/utils/exercise-helpers';
import type { useExerciseSuggestions } from '@/hooks/useExerciseSuggestions';

interface StrengthExercisesEditSectionProps {
  exercises: ExerciseForm[];
  updateExercise: (id: string, updates: Partial<ExerciseForm>) => void;
  removeExercise: (id: string) => void;
  addExercise: () => void;
  moveExercise: (index: number, direction: -1 | 1) => void;
  suggestions: ReturnType<typeof useExerciseSuggestions>;
}

// eslint-disable-next-line max-lines-per-function -- JSX-heavy exercise editor
export function StrengthExercisesEditSection({
  exercises,
  updateExercise,
  removeExercise,
  addExercise,
  moveExercise,
  suggestions,
}: StrengthExercisesEditSectionProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
        Übungen ({exercises.filter((e) => e.name.trim()).length})
      </h2>

      {/* eslint-disable-next-line max-lines-per-function, complexity -- exercise card JSX */}
      {exercises.map((exercise, exIndex) => (
        <Card key={exercise.id} elevation="raised" padding="spacious">
          <CardBody>
            <div className="space-y-4">
              {/* Exercise Header */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Dumbbell className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  <span className="text-xs font-medium text-[var(--color-text-muted)]">
                    Übung {exIndex + 1}
                  </span>
                  {exercise.name && (
                    <Badge variant={categoryBadgeVariant[exercise.category] ?? 'neutral'} size="xs">
                      {CATEGORY_LABELS[exercise.category] ?? exercise.category}
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveExercise(exIndex, -1)}
                    disabled={exIndex === 0}
                    aria-label="Nach oben"
                    className="!p-1"
                  >
                    <GripVertical className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                  </Button>
                  {exercise.name && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        updateExercise(exercise.id, { collapsed: !exercise.collapsed })
                      }
                      aria-label={exercise.collapsed ? 'Aufklappen' : 'Zuklappen'}
                    >
                      {exercise.collapsed ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronUp className="w-4 h-4" />
                      )}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeExercise(exercise.id)}
                    aria-label="Übung entfernen"
                  >
                    <Trash2 className="w-4 h-4 text-[var(--color-text-error)]" />
                  </Button>
                </div>
              </div>

              {/* Expanded details */}
              {!exercise.collapsed && (
                <>
                  {/* Name + suggestions */}
                  <div
                    className="relative"
                    ref={
                      suggestions.showSuggestions === exercise.id
                        ? suggestions.suggestionsRef
                        : undefined
                    }
                  >
                    <Input
                      value={exercise.name}
                      onChange={(e) => {
                        updateExercise(exercise.id, { name: e.target.value });
                        suggestions.setShowSuggestions(exercise.id);
                      }}
                      onFocus={() => suggestions.setShowSuggestions(exercise.id)}
                      placeholder="Übungsname (z.B. Kniebeugen)"
                      inputSize="md"
                    />
                    {suggestions.showSuggestions === exercise.id &&
                      /* prettier-ignore */
                      <div className="absolute z-10 mt-1 w-full rounded-[var(--radius-component-md)] bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] shadow-[var(--shadow-md)] max-h-48 overflow-y-auto"> {/* // ds-ok */}
                        {suggestions.getFilteredSuggestions(exercise.name).map((ex) => (
                          <button
                            key={ex.id}
                            type="button"
                            className="w-full text-left px-3 py-2.5 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-muted)] transition-colors duration-150 motion-reduce:transition-none flex items-center justify-between"
                            onClick={() => suggestions.selectSuggestion(exercise.id, ex)}
                          >
                            <span>{ex.name}</span>
                            <Badge
                              variant={categoryBadgeVariant[ex.category] ?? 'neutral'}
                              size="xs"
                            >
                              {CATEGORY_LABELS[ex.category] ?? ex.category}
                            </Badge>
                          </button>
                        ))}
                        {suggestions.getFilteredSuggestions(exercise.name).length === 0 && (
                          <p className="px-3 py-2.5 text-xs text-[var(--color-text-muted)]">
                            Keine Übung gefunden.
                          </p>
                        )}
                      </div>}
                  </div>

                  {/* Category + Type + Sets/Reps/Weight + Notes */}
                  {exercise.name && (
                    <>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-[var(--color-text-muted)]">Kategorie:</span>
                        {CATEGORY_OPTIONS.map((cat) => (
                          <button
                            key={cat.value}
                            type="button"
                            onClick={() => updateExercise(exercise.id, { category: cat.value })}
                            className={`px-2.5 py-1 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none ${
                              exercise.category === cat.value
                                ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                                : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
                            }`}
                          >
                            {cat.label}
                          </button>
                        ))}
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-[var(--color-text-muted)]">Typ:</span>
                        {EXERCISE_TYPE_OPTIONS.map((t) => (
                          <button
                            key={t.value}
                            type="button"
                            onClick={() => updateExercise(exercise.id, { exercise_type: t.value })}
                            className={`px-2.5 py-1 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none ${
                              exercise.exercise_type === t.value
                                ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                                : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
                            }`}
                          >
                            {t.label}
                          </button>
                        ))}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
                        <div>
                          <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                            Sätze
                          </Label>
                          <NumberInput
                            value={exercise.sets}
                            onChange={(val) => updateExercise(exercise.id, { sets: val })}
                            min={1}
                            max={20}
                            step={1}
                            inputSize="sm"
                            decrementLabel="Sätze reduzieren"
                            incrementLabel="Sätze erhöhen"
                          />
                        </div>
                        <div>
                          <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                            Reps
                          </Label>
                          <NumberInput
                            value={exercise.reps}
                            onChange={(val) => updateExercise(exercise.id, { reps: val })}
                            min={1}
                            max={100}
                            step={1}
                            inputSize="sm"
                            decrementLabel="Reps reduzieren"
                            incrementLabel="Reps erhöhen"
                          />
                        </div>
                        <div>
                          <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                            Gewicht (kg)
                          </Label>
                          <NumberInput
                            value={exercise.weight_kg}
                            onChange={(val) => updateExercise(exercise.id, { weight_kg: val })}
                            min={0}
                            max={999}
                            step={2.5}
                            inputSize="sm"
                            decrementLabel="Gewicht reduzieren"
                            incrementLabel="Gewicht erhöhen"
                          />
                        </div>
                      </div>
                      <div>
                        <Input
                          value={exercise.notes}
                          onChange={(e) => updateExercise(exercise.id, { notes: e.target.value })}
                          placeholder="Notizen (optional)"
                          inputSize="sm"
                        />
                      </div>
                    </>
                  )}
                </>
              )}

              {/* Collapsed summary */}
              {exercise.collapsed && exercise.name && (
                <p className="text-sm text-[var(--color-text-muted)]">
                  {exercise.sets}×{exercise.reps}
                  {exercise.weight_kg > 0 ? ` @ ${exercise.weight_kg} kg` : ''}
                  {exercise.notes ? ` · ${exercise.notes}` : ''}
                </p>
              )}
            </div>
          </CardBody>
        </Card>
      ))}

      <Button variant="secondary" onClick={addExercise} className="w-full">
        <Plus className="w-4 h-4 mr-2" />
        Übung hinzufügen
      </Button>
    </div>
  );
}
