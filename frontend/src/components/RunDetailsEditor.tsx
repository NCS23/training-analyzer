import { Input, Select, Button, Label } from '@nordlig/components';
import { Plus, Trash2 } from 'lucide-react';
import type { RunDetails, RunInterval } from '@/api/weekly-plan';
import { lapTypeLabels } from '@/constants/training';
import { SEGMENT_TYPES } from '@/constants/taxonomy';

// --- Constants ---

const SEGMENT_OPTIONS = SEGMENT_TYPES.map((key) => ({
  value: key,
  label: lapTypeLabels[key] ?? key,
}));

/** Types that show the interval builder. */
const INTERVAL_RUN_TYPES = new Set(['intervals', 'repetitions', 'fartlek']);

function emptyInterval(): RunInterval {
  return {
    type: 'work',
    duration_minutes: 3,
    target_pace_min: null,
    target_pace_max: null,
    target_hr_min: null,
    target_hr_max: null,
    repeats: 1,
  };
}

// --- Sub-Components ---

interface IntervalRowProps {
  interval: RunInterval;
  index: number;
  onChange: (index: number, updated: RunInterval) => void;
  onRemove: (index: number) => void;
}

function IntervalRow({ interval, index, onChange, onRemove }: IntervalRowProps) {
  const update = (partial: Partial<RunInterval>) => {
    onChange(index, { ...interval, ...partial });
  };

  return (
    <div className="flex items-start gap-1.5">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 flex-1">
        <Select
          options={SEGMENT_OPTIONS}
          value={interval.type}
          onChange={(val) => {
            if (val) update({ type: val as RunInterval['type'] });
          }}
          inputSize="sm"
          aria-label={`Segment ${index + 1} Typ`}
        />
        <Input
          type="number"
          min={0.5}
          max={180}
          step={0.5}
          value={interval.duration_minutes}
          onChange={(e) => update({ duration_minutes: Number(e.target.value) || 1 })}
          inputSize="sm"
          placeholder="Min"
          aria-label={`Segment ${index + 1} Dauer`}
        />
        <Input
          type="text"
          value={interval.target_pace_min ?? ''}
          onChange={(e) => update({ target_pace_min: e.target.value || null })}
          inputSize="sm"
          placeholder="Pace M:SS"
          aria-label={`Segment ${index + 1} Pace`}
        />
        <Input
          type="number"
          min={1}
          max={50}
          value={interval.repeats}
          onChange={(e) => update({ repeats: Number(e.target.value) || 1 })}
          inputSize="sm"
          placeholder="Wdh."
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
  );
}

// --- Main Component ---

interface RunDetailsEditorProps {
  runDetails: RunDetails | null;
  runType: string | null;
  onChange: (details: RunDetails | null) => void;
}

export function RunDetailsEditor({ runDetails, runType, onChange }: RunDetailsEditorProps) {
  if (!runType) {
    return (
      <p className="text-xs text-[var(--color-text-muted)] italic">
        Wird automatisch berechnet
      </p>
    );
  }

  const showIntervals = INTERVAL_RUN_TYPES.has(runType);

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

  const handleIntervalChange = (index: number, updated: RunInterval) => {
    const intervals = [...(details.intervals ?? [])];
    intervals[index] = updated;
    update({ intervals });
  };

  const handleIntervalRemove = (index: number) => {
    const intervals = (details.intervals ?? []).filter((_, i) => i !== index);
    update({ intervals: intervals.length > 0 ? intervals : null });
  };

  const handleIntervalAdd = () => {
    const intervals = [...(details.intervals ?? []), emptyInterval()];
    update({ intervals });
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

      {/* Interval builder */}
      {showIntervals && (
        <div className="space-y-2">
          <Label className="text-xs">Segmente</Label>

          {(details.intervals ?? []).length === 0 && (
            <p className="text-xs text-[var(--color-text-muted)] italic">
              Keine Segmente — wird automatisch berechnet
            </p>
          )}

          {(details.intervals ?? []).map((interval, i) => (
            <IntervalRow
              key={i}
              interval={interval}
              index={i}
              onChange={handleIntervalChange}
              onRemove={handleIntervalRemove}
            />
          ))}

          <Button
            variant="ghost"
            size="sm"
            onClick={handleIntervalAdd}
            type="button"
            className="min-h-[44px]"
          >
            <Plus className="w-4 h-4 mr-1" />
            Segment
          </Button>
        </div>
      )}

      {!runDetails && (
        <p className="text-[10px] text-[var(--color-text-muted)] italic">
          Leer lassen = automatische Berechnung aus Ziel und Volumen
        </p>
      )}
    </div>
  );
}
