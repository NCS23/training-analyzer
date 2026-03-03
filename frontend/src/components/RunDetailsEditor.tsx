import { useState, useEffect } from 'react';
import { Input, Select, Button, Label } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import type { RunDetails } from '@/api/weekly-plan';
import type { Segment, SegmentType } from '@/api/segment';
import { createEmptySegment } from '@/api/segment';
import { lapTypeLabels } from '@/constants/training';
import { SEGMENT_TYPES } from '@/constants/taxonomy';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';

// --- Constants ---

const SEGMENT_OPTIONS = SEGMENT_TYPES.map((key) => ({
  value: key,
  label: lapTypeLabels[key] ?? key,
}));

/** Segment types that show the exercise picker. */
const EXERCISE_SEGMENT_TYPES = new Set<string>(['drills', 'strides']);

type TargetMode = 'duration' | 'distance';

// --- Hooks ---

function useDrillExercises() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  useEffect(() => {
    let cancelled = false;
    listExercises({ category: 'drills' })
      .then((res) => {
        if (!cancelled) setExercises(res.exercises);
      })
      .catch(() => {
        /* ignore — optional enrichment */
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return exercises;
}

// --- Sub-Components ---

interface SegmentEditorRowProps {
  segment: Segment;
  index: number;
  drillExercises: Exercise[];
  onChange: (index: number, updated: Segment) => void;
  onRemove: (index: number) => void;
}

function SegmentEditorRow({
  segment,
  index,
  drillExercises,
  onChange,
  onRemove,
}: SegmentEditorRowProps) {
  const update = (partial: Partial<Segment>) => {
    onChange(index, { ...segment, ...partial });
  };

  const targetMode: TargetMode = segment.target_distance_km != null ? 'distance' : 'duration';
  const showExercisePicker = EXERCISE_SEGMENT_TYPES.has(segment.segment_type);

  const exerciseOptions = drillExercises.map((ex) => ({
    value: ex.name,
    label: ex.name,
  }));

  const handleTargetModeSwitch = (mode: TargetMode) => {
    if (mode === 'distance') {
      update({ target_duration_minutes: null, target_distance_km: 0.4 });
    } else {
      update({ target_distance_km: null, target_duration_minutes: 3 });
    }
  };

  return (
    <div className="rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] p-2.5 space-y-2">
      {/* Row 1: Type + Repeats + Delete */}
      <div className="flex items-end gap-1.5">
        <div className="flex-1 min-w-0">
          <Label className="text-[10px] mb-0.5">Typ</Label>
          <Select
            options={SEGMENT_OPTIONS}
            value={segment.segment_type}
            onChange={(val) => {
              if (val) update({ segment_type: val as SegmentType });
            }}
            inputSize="sm"
            aria-label={`Segment ${index + 1} Typ`}
          />
        </div>
        <div className="w-16 shrink-0">
          <Label className="text-[10px] mb-0.5">Wdh.</Label>
          <Input
            type="number"
            min={1}
            max={50}
            value={segment.repeats}
            onChange={(e) => update({ repeats: Number(e.target.value) || 1 })}
            inputSize="sm"
            aria-label={`Segment ${index + 1} Wiederholungen`}
          />
        </div>
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-error)] transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)] rounded-[var(--radius-component-sm)]"
          aria-label={`Segment ${index + 1} entfernen`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Row 2: Duration/Distance toggle + value */}
      <div>
        <div className="flex items-center gap-1.5 mb-0.5">
          <button
            type="button"
            onClick={() => handleTargetModeSwitch('duration')}
            className={`text-[10px] px-1.5 py-0.5 rounded-[var(--radius-component-sm)] transition-colors motion-reduce:transition-none ${
              targetMode === 'duration'
                ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
            }`}
          >
            Dauer
          </button>
          <button
            type="button"
            onClick={() => handleTargetModeSwitch('distance')}
            className={`text-[10px] px-1.5 py-0.5 rounded-[var(--radius-component-sm)] transition-colors motion-reduce:transition-none ${
              targetMode === 'distance'
                ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
            }`}
          >
            Distanz
          </button>
        </div>
        {targetMode === 'duration' ? (
          <Input
            type="number"
            min={0.5}
            max={180}
            step={0.5}
            value={segment.target_duration_minutes ?? ''}
            onChange={(e) => update({ target_duration_minutes: Number(e.target.value) || 1 })}
            inputSize="sm"
            placeholder="z.B. 3 min"
            aria-label={`Segment ${index + 1} Dauer`}
          />
        ) : (
          <Input
            type="number"
            min={0.01}
            max={100}
            step={0.1}
            value={segment.target_distance_km ?? ''}
            onChange={(e) => update({ target_distance_km: Number(e.target.value) || 0.4 })}
            inputSize="sm"
            placeholder="z.B. 0.4 km"
            aria-label={`Segment ${index + 1} Distanz`}
          />
        )}
      </div>

      {/* Row 3: Pace range */}
      <div>
        <Label className="text-[10px] mb-0.5">Pace (M:SS / km)</Label>
        <div className="grid grid-cols-2 gap-1.5">
          <Input
            type="text"
            value={segment.target_pace_min ?? ''}
            onChange={(e) => update({ target_pace_min: e.target.value || null })}
            inputSize="sm"
            placeholder="schnell"
            aria-label={`Segment ${index + 1} Pace schnell`}
          />
          <Input
            type="text"
            value={segment.target_pace_max ?? ''}
            onChange={(e) => update({ target_pace_max: e.target.value || null })}
            inputSize="sm"
            placeholder="langsam"
            aria-label={`Segment ${index + 1} Pace langsam`}
          />
        </div>
      </div>

      {/* Row 4: HR range */}
      <div>
        <Label className="text-[10px] mb-0.5">Herzfrequenz (bpm)</Label>
        <div className="grid grid-cols-2 gap-1.5">
          <Input
            type="number"
            min={60}
            max={220}
            value={segment.target_hr_min ?? ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              update({ target_hr_min: val });
            }}
            inputSize="sm"
            placeholder="Min"
            aria-label={`Segment ${index + 1} HR Min`}
          />
          <Input
            type="number"
            min={60}
            max={220}
            value={segment.target_hr_max ?? ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              update({ target_hr_max: val });
            }}
            inputSize="sm"
            placeholder="Max"
            aria-label={`Segment ${index + 1} HR Max`}
          />
        </div>
      </div>

      {/* Row 5: Exercise picker (only for drills/strides) */}
      {showExercisePicker && (
        <div>
          <Label className="text-[10px] mb-0.5">Übung</Label>
          <Select
            options={exerciseOptions}
            value={segment.exercise_name ?? ''}
            onChange={(val) => update({ exercise_name: val || null })}
            inputSize="sm"
            placeholder="Übung wählen"
            aria-label={`Segment ${index + 1} Übung`}
          />
        </div>
      )}

      {/* Row 6: Notes */}
      <div>
        <Label className="text-[10px] mb-0.5">Notiz</Label>
        <Input
          type="text"
          value={segment.notes ?? ''}
          onChange={(e) => update({ notes: e.target.value || null })}
          inputSize="sm"
          placeholder="z.B. bergauf, Fokus Kniehub"
          aria-label={`Segment ${index + 1} Notiz`}
        />
      </div>
    </div>
  );
}

// --- Main Component ---

interface RunDetailsEditorProps {
  runDetails: RunDetails | null;
  runType: string | null;
  onChange: (details: RunDetails | null) => void;
}

export function RunDetailsEditor({ runDetails, runType, onChange }: RunDetailsEditorProps) {
  const drillExercises = useDrillExercises();

  if (!runType) {
    return (
      <p className="text-xs text-[var(--color-text-muted)] italic">Wird automatisch berechnet</p>
    );
  }

  // Ensure we have a RunDetails object to work with
  const details: RunDetails = runDetails ?? {
    run_type: runType as RunDetails['run_type'],
    target_duration_minutes: null,
    target_pace_min: null,
    target_pace_max: null,
    target_hr_min: null,
    target_hr_max: null,
    intervals: null,
  };

  const update = (partial: Partial<RunDetails>) => {
    onChange({ ...details, ...partial });
  };

  const handleSegmentChange = (index: number, updated: Segment) => {
    const segments = [...(details.segments ?? [])];
    segments[index] = updated;
    update({ segments, intervals: null });
  };

  const handleSegmentRemove = (index: number) => {
    const segments = (details.segments ?? [])
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, position: i }));
    update({ segments: segments.length > 0 ? segments : null, intervals: null });
  };

  const handleSegmentAdd = () => {
    const pos = (details.segments ?? []).length;
    const segments = [
      ...(details.segments ?? []),
      createEmptySegment(pos, { target_duration_minutes: 3 }),
    ];
    update({ segments, intervals: null });
  };

  return (
    <div className="space-y-3">
      {/* Duration */}
      <div>
        <Label className="text-xs mb-1">Dauer (min)</Label>
        <Input
          type="number"
          min={5}
          max={360}
          value={details.target_duration_minutes ?? ''}
          onChange={(e) => {
            const val = e.target.value ? Number(e.target.value) : null;
            update({ target_duration_minutes: val });
          }}
          inputSize="sm"
          placeholder="z.B. 45"
          aria-label="Dauer in Minuten"
        />
      </div>

      {/* Pace range */}
      <div>
        <Label className="text-xs mb-1">Pace (M:SS / km)</Label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="text"
            value={details.target_pace_min ?? ''}
            onChange={(e) => update({ target_pace_min: e.target.value || null })}
            inputSize="sm"
            placeholder="schnell 4:30"
            aria-label="Pace schnell"
          />
          <Input
            type="text"
            value={details.target_pace_max ?? ''}
            onChange={(e) => update({ target_pace_max: e.target.value || null })}
            inputSize="sm"
            placeholder="langsam 5:30"
            aria-label="Pace langsam"
          />
        </div>
      </div>

      {/* HR range */}
      <div>
        <Label className="text-xs mb-1">Herzfrequenz (bpm)</Label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="number"
            min={60}
            max={220}
            value={details.target_hr_min ?? ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              update({ target_hr_min: val });
            }}
            inputSize="sm"
            placeholder="Min"
            aria-label="Herzfrequenz Min"
          />
          <Input
            type="number"
            min={60}
            max={220}
            value={details.target_hr_max ?? ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null;
              update({ target_hr_max: val });
            }}
            inputSize="sm"
            placeholder="Max"
            aria-label="Herzfrequenz Max"
          />
        </div>
      </div>

      {/* Segment builder — available for ALL run types */}
      <div className="space-y-2">
        <Label className="text-xs">Segmente</Label>

        {(details.segments ?? []).length === 0 && (
          <p className="text-xs text-[var(--color-text-muted)] italic">
            Keine Segmente — optional für strukturierte Workouts
          </p>
        )}

        {(details.segments ?? []).map((segment, i) => (
          <SegmentEditorRow
            key={i}
            segment={segment}
            index={i}
            drillExercises={drillExercises}
            onChange={handleSegmentChange}
            onRemove={handleSegmentRemove}
          />
        ))}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleSegmentAdd}
          type="button"
          className="min-h-[44px]"
        >
          <Plus className="w-4 h-4 mr-1" />
          Segment
        </Button>
      </div>

      {!runDetails && (
        <p className="text-[10px] text-[var(--color-text-muted)] italic">
          Leer lassen = automatische Berechnung aus Ziel und Volumen
        </p>
      )}
    </div>
  );
}
