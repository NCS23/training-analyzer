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

const categoryLabels: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
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

type Exercise = {
  name: string;
  category: string;
  sets: Array<{ reps: number; weight_kg: number; status: string }>;
};

interface SessionExercisesSectionProps {
  exercises: Exercise[];
  sessionId: number;
  isEditing: boolean;
  editorRef: React.RefObject<StrengthExercisesEditorRef | null>;
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
            {exercises.map((ex, exIdx) => (
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
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-10 sticky left-0 z-10 bg-[var(--color-table-header-bg)]">
                          #
                        </TableHead>
                        <TableHead>Wdh.</TableHead>
                        <TableHead>Gewicht</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {ex.sets.map((s, sIdx) => (
                        <TableRow key={sIdx}>
                          <TableCell className="text-[var(--color-text-muted)]">
                            {sIdx + 1}
                          </TableCell>
                          <TableCell>{s.reps}</TableCell>
                          <TableCell>{s.weight_kg > 0 ? `${s.weight_kg} kg` : '-'}</TableCell>
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
            ))}
          </CardBody>
        </Card>
      )}
    </section>
  );
}
