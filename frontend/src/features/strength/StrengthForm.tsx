import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  DatePicker,
  Label,
  NumberInput,
  Slider,
  Textarea,
  FileUpload,
  Alert,
  AlertDescription,
  Spinner,
} from '@nordlig/components';
import { Plus } from 'lucide-react';
import type { ExerciseInput, SetType } from '@/api/strength';
import { createStrengthSession } from '@/api/strength';
import type { Exercise } from '@/api/exercises';
import { listExercises } from '@/api/exercises';
import { ExerciseCard } from './ExerciseCard';
import { formatLocalDate } from '@/utils/weeklyPlanUtils';

const defaultExercise: ExerciseInput = {
  name: '',
  category: 'push',
  sets: [{ type: 'weight_reps', reps: 8, weight_kg: 0, status: 'completed' }],
};

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
export function StrengthForm() {
  const navigate = useNavigate();

  const [date, setDate] = useState<Date>(new Date());
  const [duration, setDuration] = useState(60);
  const [rpe, setRpe] = useState(5);
  const [notes, setNotes] = useState('');
  const [exercises, setExercises] = useState<ExerciseInput[]>([{ ...defaultExercise }]);
  const [setTypes, setSetTypes] = useState<SetType[]>(['weight_reps']);

  const [trainingFile, setTrainingFile] = useState<File | null>(null);
  const [exerciseLibrary, setExerciseLibrary] = useState<Exercise[]>([]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listExercises()
      .then((res) => setExerciseLibrary(res.exercises))
      .catch(() => {
        /* Autocomplete is optional — fail silently */
      });
  }, []);

  const handleExerciseChange = useCallback((idx: number, updated: ExerciseInput) => {
    setExercises((prev) => {
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  }, []);

  const handleSetTypeChange = useCallback((idx: number, newSetType: SetType) => {
    setSetTypes((prev) => {
      const next = [...prev];
      next[idx] = newSetType;
      return next;
    });
  }, []);

  const handleExerciseRemove = useCallback((idx: number) => {
    setExercises((prev) => prev.filter((_, i) => i !== idx));
    setSetTypes((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const handleAddExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      {
        ...defaultExercise,
        sets: [{ type: 'weight_reps', reps: 8, weight_kg: 0, status: 'completed' }],
      },
    ]);
    setSetTypes((prev) => [...prev, 'weight_reps']);
  }, []);

  const canSubmit = exercises.length > 0 && exercises.every((ex) => ex.name.trim().length > 0);

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;

    setSaving(true);
    setError(null);

    try {
      const result = await createStrengthSession({
        date: formatLocalDate(date),
        duration_minutes: duration,
        exercises,
        notes: notes.trim() || undefined,
        rpe,
        trainingFile: trainingFile || undefined,
      });

      if (result.success) {
        navigate(`/sessions/${result.session_id}`, { state: { uploaded: true } });
      }
    } catch (err) {
      setError('Fehler beim Speichern: ' + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }, [canSubmit, date, duration, exercises, notes, rpe, trainingFile, navigate]);

  return (
    <div className="space-y-6">
      {/* Error */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Training Meta */}
      <Card elevation="raised">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Training</h2>
        </CardHeader>
        <CardBody className="space-y-4">
          <FileUpload
            accept=".csv,.fit,application/octet-stream"
            onUpload={(files) => {
              if (files[0]) setTrainingFile(files[0]);
            }}
            onRemove={() => setTrainingFile(null)}
            instructionText={
              trainingFile ? trainingFile.name : 'Optional: Datei von Sportuhr hochladen'
            }
            subText="CSV, FIT — Herzfrequenz und Dauer werden automatisch übernommen"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Datum</Label>
              <DatePicker
                value={date}
                onChange={(d) => {
                  if (d) setDate(d);
                }}
                maxDate={new Date()}
                placeholder="Datum wählen"
              />
            </div>
            <div className="space-y-2">
              <Label>Dauer (min)</Label>
              <NumberInput
                value={duration}
                onChange={setDuration}
                min={1}
                max={300}
                step={5}
                aria-label="Trainingsdauer in Minuten"
                incrementLabel="5 Minuten mehr"
                decrementLabel="5 Minuten weniger"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>RPE (Anstrengung): {rpe}</Label>
            <Slider
              value={[rpe]}
              onValueChange={([val]) => setRpe(val)}
              min={1}
              max={10}
              step={1}
              showValue
              aria-label="Rate of Perceived Exertion"
            />
          </div>
        </CardBody>
      </Card>

      {/* Exercises */}
      <Card elevation="raised">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Übungen ({exercises.length})
          </h2>
        </CardHeader>
        <CardBody className="space-y-4">
          {exercises.map((ex, idx) => (
            <ExerciseCard
              key={idx}
              index={idx}
              exercise={ex}
              setType={setTypes[idx] || 'weight_reps'}
              onSetTypeChange={handleSetTypeChange}
              onChange={handleExerciseChange}
              onRemove={handleExerciseRemove}
              canRemove={exercises.length > 1}
              exerciseLibrary={exerciseLibrary}
            />
          ))}

          <Button variant="ghost" size="sm" onClick={handleAddExercise} className="w-full">
            <Plus className="w-3.5 h-3.5 mr-1" />
            Übung hinzufügen
          </Button>
        </CardBody>
      </Card>

      {/* Notes + Submit */}
      <Card elevation="raised">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Notizen</h2>
        </CardHeader>
        <CardBody>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Wie war das Training? (optional)"
          />
        </CardBody>
        <CardFooter className="justify-end">
          <Button variant="primary" onClick={handleSubmit} disabled={!canSubmit || saving}>
            {saving ? (
              <span className="flex items-center gap-2">
                <Spinner size="sm" aria-hidden="true" />
                Speichere...
              </span>
            ) : (
              'Session anlegen'
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
