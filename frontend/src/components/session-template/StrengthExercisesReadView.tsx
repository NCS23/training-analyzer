/**
 * Read-only view of strength exercises in a session template.
 */
import { Card, CardBody, Badge } from '@nordlig/components';
import { categoryBadgeVariant } from '@/constants/training';
import { CATEGORY_LABELS, EXERCISE_TYPE_OPTIONS } from '@/utils/exercise-helpers';
import type { ExerciseForm } from '@/utils/exercise-helpers';

interface StrengthExercisesReadViewProps {
  exercises: ExerciseForm[];
}

export function StrengthExercisesReadView({ exercises }: StrengthExercisesReadViewProps) {
  const validExercises = exercises.filter((e) => e.name.trim());
  return (
    <Card elevation="raised" padding="spacious">
      <CardBody>
        <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">
          Übungen ({validExercises.length})
        </h2>
        {validExercises.length === 0 ? (
          <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
            Keine Übungen definiert.
          </p>
        ) : (
          <div className="space-y-2">
            {validExercises.map((exercise, idx) => (
              <div
                key={exercise.id ?? `ro-${idx}`}
                className="py-2 px-3 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)] space-y-1"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm font-medium text-[var(--color-text-base)] truncate">
                      {exercise.name}
                    </span>
                    <Badge variant={categoryBadgeVariant[exercise.category] ?? 'neutral'} size="xs">
                      {CATEGORY_LABELS[exercise.category] ?? exercise.category}
                    </Badge>
                    {exercise.exercise_type !== 'kraft' && (
                      <Badge variant="neutral" size="xs">
                        {EXERCISE_TYPE_OPTIONS.find((t) => t.value === exercise.exercise_type)
                          ?.label ?? exercise.exercise_type}
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm text-[var(--color-text-muted)] shrink-0 ml-2">
                    {exercise.sets}×{exercise.reps}
                    {exercise.weight_kg > 0 ? ` @ ${exercise.weight_kg} kg` : ''}
                  </span>
                </div>
                {exercise.notes && (
                  <p className="text-xs text-[var(--color-text-muted)] italic">{exercise.notes}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
