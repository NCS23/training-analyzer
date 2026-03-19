import {
  Card,
  CardHeader,
  CardBody,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';
import { categoryBadgeVariant } from '@/constants/training';
import { StrengthExercisesEditor } from '@/components/StrengthExercisesEditor';
import type { StrengthExercisesEditorRef } from '@/components/StrengthExercisesEditor';
import type { ExerciseData } from '@/components/StrengthExercisesEditor';

const categoryLabels: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Lauf-ABC',
};

const statusLabels: Record<string, string> = {
  completed: 'Fertig',
  reduced: 'Reduziert',
  skipped: 'Ausgelassen',
};

const statusVariant: Record<string, 'success' | 'warning' | 'info'> = {
  completed: 'success',
  reduced: 'warning',
  skipped: 'info',
};

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

interface SessionExercisesSectionProps {
  exercises: ExerciseData[];
  sessionId: number;
  isEditing: boolean;
  editorRef: React.RefObject<StrengthExercisesEditorRef | null>;
}

function detectExerciseColumns(sets: ExerciseData['sets']) {
  let hasReps = false;
  let hasWeight = false;
  let hasDuration = false;
  let hasDistance = false;
  for (const s of sets) {
    if (s.reps != null && s.reps > 0) hasReps = true;
    if (s.weight_kg != null && s.weight_kg > 0) hasWeight = true;
    if (s.duration_sec != null && s.duration_sec > 0) hasDuration = true;
    if (s.distance_m != null && s.distance_m > 0) hasDistance = true;
  }
  // If no fields detected at all, default to reps+weight for backward compat
  if (!hasReps && !hasWeight && !hasDuration && !hasDistance) {
    hasReps = true;
    hasWeight = true;
  }
  return { hasReps, hasWeight, hasDuration, hasDistance };
}

export function SessionExercisesSection({
  exercises,
  sessionId,
  isEditing,
  editorRef,
}: SessionExercisesSectionProps) {
  return (
    <section aria-label="Übungen">
      {isEditing ? (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <h2 className="text-base font-semibold text-[var(--color-text-base)] mb-4">
              Übungen ({exercises.length})
            </h2>
            <StrengthExercisesEditor ref={editorRef} sessionId={sessionId} exercises={exercises} />
          </CardBody>
        </Card>
      ) : (
        <Card elevation="raised">
          <CardHeader>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Übungen ({exercises.length})
            </h2>
          </CardHeader>
          <CardBody className="space-y-4">
            {exercises.map((ex, exIdx) => {
              const cols = detectExerciseColumns(ex.sets);
              return (
                <div key={exIdx} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--color-text-base)]">
                      {ex.name}
                    </span>
                    <Badge variant={categoryBadgeVariant[ex.category] ?? 'neutral'} size="xs">
                      {categoryLabels[ex.category] ?? ex.category}
                    </Badge>
                  </div>
                  <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
                    <Table className="table-fixed">
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-[8%] sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                            #
                          </TableHead>
                          {cols.hasReps && <TableHead className="w-[22%]">Wdh.</TableHead>}
                          {cols.hasWeight && <TableHead className="w-[30%]">Gewicht</TableHead>}
                          {cols.hasDuration && <TableHead className="w-[30%]">Dauer</TableHead>}
                          {cols.hasDistance && <TableHead className="w-[30%]">Distanz</TableHead>}
                          <TableHead className="w-[22%]">Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {ex.sets.map((s, sIdx) => (
                          <TableRow key={sIdx}>
                            <TableCell className="text-[var(--color-text-muted)]">
                              {sIdx + 1}
                            </TableCell>
                            {cols.hasReps && <TableCell>{s.reps ?? '-'}</TableCell>}
                            {cols.hasWeight && (
                              <TableCell>
                                {(s.weight_kg ?? 0) > 0 ? `${s.weight_kg} kg` : '-'}
                              </TableCell>
                            )}
                            {cols.hasDuration && (
                              <TableCell>
                                {(s.duration_sec ?? 0) > 0
                                  ? formatDuration(s.duration_sec ?? 0)
                                  : '-'}
                              </TableCell>
                            )}
                            {cols.hasDistance && (
                              <TableCell>
                                {(s.distance_m ?? 0) > 0 ? `${s.distance_m} m` : '-'}
                              </TableCell>
                            )}
                            <TableCell>
                              <Badge variant={statusVariant[s.status] ?? 'info'} size="xs">
                                {statusLabels[s.status] ?? s.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              );
            })}
          </CardBody>
        </Card>
      )}
    </section>
  );
}
