/**
 * Inline-Editor für Übungen einer gespeicherten Kraftsession.
 * Verwendet ExerciseFormSection — identische UI wie die Erfassungsseite.
 * Die Eltern-Komponente ruft save() über den Ref auf.
 */
import { useState, useImperativeHandle, forwardRef } from 'react';
import { useToast } from '@nordlig/components';
import { updateStrengthExercises } from '@/api/strength';
import type { ExerciseCategory, SetStatus } from '@/api/strength';
import { ExerciseFormSection } from '@/components/ExerciseFormSection';
import { genId } from '@/components/exercise-form-helpers';
import type { ExerciseForm } from '@/components/exercise-form-helpers';

// --- Types ---

export interface ExerciseData {
  name: string;
  category: string;
  sets: Array<{ reps: number; weight_kg: number; status: string }>;
}

export interface StrengthExercisesEditorRef {
  save: () => Promise<ExerciseData[] | null>;
}

interface StrengthExercisesEditorProps {
  sessionId: number;
  exercises: ExerciseData[];
}

// --- Helpers ---

function toForms(exercises: ExerciseData[]): ExerciseForm[] {
  return exercises.map((ex) => ({
    id: genId('edit'),
    name: ex.name,
    category: ex.category as ExerciseCategory,
    sets: ex.sets.map((s) => ({
      id: genId('set'),
      reps: s.reps,
      weight_kg: s.weight_kg,
      status: (s.status || 'completed') as SetStatus,
    })),
  }));
}

// --- Component ---

export const StrengthExercisesEditor = forwardRef<
  StrengthExercisesEditorRef,
  StrengthExercisesEditorProps
>(function StrengthExercisesEditor({ sessionId, exercises: initialExercises }, ref) {
  const { toast } = useToast();
  const [exercises, setExercises] = useState<ExerciseForm[]>(() => toForms(initialExercises));

  // Expose save() to parent via ref
  useImperativeHandle(ref, () => ({
    save: async () => {
      const valid = exercises.every((ex) => ex.name.trim().length > 0 && ex.sets.length > 0);
      if (!valid) {
        toast({
          title: 'Jede Übung braucht einen Namen und mindestens einen Satz.',
          variant: 'error',
        });
        return null;
      }

      const apiExercises = exercises.map((ex) => ({
        name: ex.name.trim(),
        category: ex.category,
        sets: ex.sets.map((s) => ({
          reps: s.reps,
          weight_kg: s.weight_kg,
          status: s.status,
        })),
      }));

      const result = await updateStrengthExercises(sessionId, apiExercises);
      return result.exercises;
    },
  }));

  return (
    <ExerciseFormSection exercises={exercises} setExercises={setExercises} hideTonnageSummary />
  );
});
