import { useState, useEffect } from 'react';
import { Input, Select, Button, Label } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import type { RunDetails } from '@/api/weekly-plan';
import type { Segment, SegmentType } from '@/api/segment';
import { createEmptySegment, segmentsToTopLevel } from '@/api/segment';
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
    <div className="rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] border-l-2 border-l-[var(--color-border-primary)] bg-[var(--color-bg-surface)] p-3 space-y-2.5">
      {/* Row 1: Type + Repeats */}
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
      </div>

      {/* Row 2: Duration/Distance select + value */}
      <div className="flex items-end gap-1.5">
        <div className="w-32 shrink-0">
          <Label className="text-[10px] mb-0.5">Zielwert</Label>
          <Select
            options={[
              { value: 'duration', label: 'Dauer' },
              { value: 'distance', label: 'Distanz' },
            ]}
            value={targetMode}
            onChange={(val) => {
              if (val) handleTargetModeSwitch(val as TargetMode);
            }}
            inputSize="sm"
            aria-label={`Segment ${index + 1} Zielwert-Typ`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">
            {targetMode === 'duration' ? 'Dauer (min)' : 'Distanz (km)'}
          </Label>
          {targetMode === 'duration' ? (
            <Input
              type="number"
              min={0.5}
              max={180}
              step={0.5}
              value={segment.target_duration_minutes ?? ''}
              onChange={(e) => update({ target_duration_minutes: Number(e.target.value) || 1 })}
              inputSize="sm"
              placeholder="min"
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
              placeholder="km"
              aria-label={`Segment ${index + 1} Distanz`}
            />
          )}
        </div>
      </div>

      {/* Row 3: Pace range */}
      <div>
        <Label className="text-[10px] mb-0.5">Pace (M:SS / km)</Label>
        <div className="grid grid-cols-2 gap-1.5">
          <div>
            <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">
              Von (schnell)
            </Label>
            <Input
              type="text"
              value={segment.target_pace_min ?? ''}
              onChange={(e) => update({ target_pace_min: e.target.value || null })}
              inputSize="sm"
              placeholder="4:30"
              aria-label={`Segment ${index + 1} Pace schnell`}
            />
          </div>
          <div>
            <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">
              Bis (langsam)
            </Label>
            <Input
              type="text"
              value={segment.target_pace_max ?? ''}
              onChange={(e) => update({ target_pace_max: e.target.value || null })}
              inputSize="sm"
              placeholder="5:30"
              aria-label={`Segment ${index + 1} Pace langsam`}
            />
          </div>
        </div>
      </div>

      {/* Row 4: HR range */}
      <div>
        <Label className="text-[10px] mb-0.5">Herzfrequenz (bpm)</Label>
        <div className="grid grid-cols-2 gap-1.5">
          <div>
            <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Min</Label>
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
              placeholder="130"
              aria-label={`Segment ${index + 1} HR Min`}
            />
          </div>
          <div>
            <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Max</Label>
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
              placeholder="150"
              aria-label={`Segment ${index + 1} HR Max`}
            />
          </div>
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

      {/* Delete segment */}
      <div className="flex justify-end pt-3">
        <Button
          variant="destructive-outline"
          size="sm"
          onClick={() => onRemove(index)}
          type="button"
          aria-label={`Segment ${index + 1} entfernen`}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Segment entfernen
        </Button>
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

  // Ensure we have a RunDetails object to work with.
  // Backend always provides segments[], but for new (unsaved) sessions we
  // need a sensible default with one "steady" segment.
  const defaultSegment = createEmptySegment(0, { segment_type: 'steady' });
  const details: RunDetails = runDetails ?? {
    run_type: runType as RunDetails['run_type'],
    target_duration_minutes: null,
    target_pace_min: null,
    target_pace_max: null,
    target_hr_min: null,
    target_hr_max: null,
    intervals: null,
    segments: [defaultSegment],
  };

  // Guarantee segments exist (defensive — should always be set by backend)
  const segments = details.segments?.length ? details.segments : [defaultSegment];

  /** Persist updated segments + recompute top-level convenience fields. */
  const emitChange = (newSegments: Segment[]) => {
    const topLevel = segmentsToTopLevel(newSegments);
    onChange({
      ...details,
      ...topLevel,
      segments: newSegments,
      intervals: null,
    });
  };

  // Simple mode: 1 segment → show compact form (Duration, Pace, HR)
  // Multi mode: >1 segments → show only the segment builder
  const isSimpleMode = segments.length <= 1;
  const primarySegment = segments[0];

  /** Update the primary (only) segment in simple mode. */
  const updatePrimary = (partial: Partial<Segment>) => {
    const updated = { ...primarySegment, ...partial };
    emitChange([updated]);
  };

  const handleSegmentChange = (index: number, updated: Segment) => {
    const newSegments = [...segments];
    newSegments[index] = updated;
    emitChange(newSegments);
  };

  const handleSegmentRemove = (index: number) => {
    const newSegments = segments
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, position: i }));
    // Always keep at least one segment
    if (newSegments.length === 0) {
      emitChange([createEmptySegment(0, { segment_type: 'steady' })]);
    } else {
      emitChange(newSegments);
    }
  };

  const handleSegmentAdd = () => {
    const pos = segments.length;
    emitChange([...segments, createEmptySegment(pos, { target_duration_minutes: 3 })]);
  };

  return (
    <div className="space-y-3">
      {/* Simple Mode: compact Duration / Pace / HR fields editing segments[0] */}
      {isSimpleMode && (
        <>
          {/* Duration */}
          <div>
            <Label className="text-xs mb-1">Dauer (min)</Label>
            <Input
              type="number"
              min={1}
              max={360}
              value={primarySegment.target_duration_minutes ?? ''}
              onChange={(e) => {
                const val = e.target.value ? Number(e.target.value) : null;
                updatePrimary({ target_duration_minutes: val });
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
              <div>
                <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">
                  Von (schnell)
                </Label>
                <Input
                  type="text"
                  value={primarySegment.target_pace_min ?? ''}
                  onChange={(e) => updatePrimary({ target_pace_min: e.target.value || null })}
                  inputSize="sm"
                  placeholder="4:30"
                  aria-label="Pace schnell"
                />
              </div>
              <div>
                <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">
                  Bis (langsam)
                </Label>
                <Input
                  type="text"
                  value={primarySegment.target_pace_max ?? ''}
                  onChange={(e) => updatePrimary({ target_pace_max: e.target.value || null })}
                  inputSize="sm"
                  placeholder="5:30"
                  aria-label="Pace langsam"
                />
              </div>
            </div>
          </div>

          {/* HR range */}
          <div>
            <Label className="text-xs mb-1">Herzfrequenz (bpm)</Label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Min</Label>
                <Input
                  type="number"
                  min={60}
                  max={220}
                  value={primarySegment.target_hr_min ?? ''}
                  onChange={(e) => {
                    const val = e.target.value ? Number(e.target.value) : null;
                    updatePrimary({ target_hr_min: val });
                  }}
                  inputSize="sm"
                  placeholder="130"
                  aria-label="Herzfrequenz Min"
                />
              </div>
              <div>
                <Label className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Max</Label>
                <Input
                  type="number"
                  min={60}
                  max={220}
                  value={primarySegment.target_hr_max ?? ''}
                  onChange={(e) => {
                    const val = e.target.value ? Number(e.target.value) : null;
                    updatePrimary({ target_hr_max: val });
                  }}
                  inputSize="sm"
                  placeholder="150"
                  aria-label="Herzfrequenz Max"
                />
              </div>
            </div>
          </div>
        </>
      )}

      {/* Segment builder — always visible */}
      <div className="border-t border-[var(--color-border-muted)] pt-3 mt-1 space-y-2">
        <Label className="text-xs font-semibold">Segmente</Label>

        {/* In multi-mode, show all segment rows */}
        {!isSimpleMode &&
          segments.map((segment, i) => (
            <SegmentEditorRow
              key={i}
              segment={segment}
              index={i}
              drillExercises={drillExercises}
              onChange={handleSegmentChange}
              onRemove={handleSegmentRemove}
            />
          ))}

        {/* In simple mode, show compact segment summary */}
        {isSimpleMode && (
          <div className="rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] bg-[var(--color-bg-surface)] px-3 py-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="font-medium text-[var(--color-text-base)]">
                {lapTypeLabels[primarySegment.segment_type] ?? primarySegment.segment_type}
              </span>
              {primarySegment.target_duration_minutes != null && (
                <span className="text-[var(--color-text-muted)]">
                  {primarySegment.target_duration_minutes} min
                </span>
              )}
              {primarySegment.target_pace_min && (
                <span className="text-[var(--color-text-muted)]">
                  {primarySegment.target_pace_min}
                  {primarySegment.target_pace_max ? `–${primarySegment.target_pace_max}` : ''} /km
                </span>
              )}
              {primarySegment.target_hr_min != null && (
                <span className="text-[var(--color-text-muted)]">
                  HR {primarySegment.target_hr_min}
                  {primarySegment.target_hr_max ? `–${primarySegment.target_hr_max}` : ''}
                </span>
              )}
              {!primarySegment.target_duration_minutes &&
                !primarySegment.target_pace_min &&
                primarySegment.target_hr_min == null && (
                  <span className="text-[var(--color-text-disabled)] italic">keine Vorgaben</span>
                )}
            </div>
          </div>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleSegmentAdd}
          type="button"
          className="w-full"
        >
          <Plus className="w-4 h-4 mr-1" />
          Segment hinzufügen
        </Button>
      </div>
    </div>
  );
}
