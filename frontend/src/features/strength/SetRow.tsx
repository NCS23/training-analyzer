import { NumberInput, Select, Button } from '@nordlig/components';
import { Trash2 } from 'lucide-react';
import type { SetInput, SetStatus, SetType } from '@/api/strength';
import { SET_TYPE_FIELDS } from '@/api/strength';

const statusOptions = [
  { value: 'completed', label: 'Fertig' },
  { value: 'reduced', label: 'Reduziert' },
  { value: 'skipped', label: 'Ausgelassen' },
];

interface SetRowProps {
  index: number;
  set: SetInput;
  setType: SetType;
  onChange: (index: number, set: SetInput) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}

function DurationInput({
  value,
  onChange,
  label,
}: {
  value: number;
  onChange: (sec: number) => void;
  label: string;
}) {
  const mins = Math.floor(value / 60);
  const secs = value % 60;

  return (
    <div className="flex items-center gap-1">
      <NumberInput
        value={mins}
        onChange={(m) => onChange(m * 60 + secs)}
        min={0}
        max={1440}
        step={1}
        inputSize="sm"
        aria-label={`${label} Minuten`}
        incrementLabel="Minute hinzufügen"
        decrementLabel="Minute entfernen"
      />
      <span className="text-xs text-[var(--color-text-muted)]">:</span>
      <NumberInput
        value={secs}
        onChange={(s) => onChange(mins * 60 + Math.min(s, 59))}
        min={0}
        max={59}
        step={1}
        inputSize="sm"
        aria-label={`${label} Sekunden`}
        incrementLabel="Sekunde hinzufügen"
        decrementLabel="Sekunde entfernen"
      />
    </div>
  );
}

function SetRowStatusControls({
  index,
  set,
  onChange,
  onRemove,
  canRemove,
}: Omit<SetRowProps, 'setType'>) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 sm:w-28 sm:flex-none sm:shrink-0">
        <Select
          options={statusOptions}
          value={set.status}
          onChange={(val) => onChange(index, { ...set, status: (val || 'completed') as SetStatus })}
          inputSize="sm"
        />
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onRemove(index)}
        disabled={!canRemove}
        aria-label={`Satz ${index + 1} entfernen`}
        className="shrink-0"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </Button>
    </div>
  );
}

export function SetRow({ index, set, setType, onChange, onRemove, canRemove }: SetRowProps) {
  const fields = SET_TYPE_FIELDS[setType];

  return (
    <div className="space-y-2 sm:space-y-0">
      {/* Zeile 1: Index + Werte-Inputs */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--color-text-muted)] w-6 shrink-0 text-center tabular-nums">
          {index + 1}
        </span>

        {fields.reps && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.reps ?? 0}
              onChange={(val) => onChange(index, { ...set, reps: val })}
              min={0}
              max={999}
              step={1}
              inputSize="sm"
              aria-label={`Satz ${index + 1} Wiederholungen`}
              incrementLabel="Wiederholung hinzufügen"
              decrementLabel="Wiederholung entfernen"
            />
          </div>
        )}

        {fields.weight && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.weight_kg ?? 0}
              onChange={(val) => onChange(index, { ...set, weight_kg: val })}
              min={0}
              max={999}
              step={2.5}
              inputSize="sm"
              aria-label={`Satz ${index + 1} Gewicht kg`}
              incrementLabel="Gewicht erhöhen"
              decrementLabel="Gewicht verringern"
            />
          </div>
        )}

        {fields.duration && (
          <div className="flex-1 min-w-0">
            <DurationInput
              value={set.duration_sec ?? 0}
              onChange={(sec) => onChange(index, { ...set, duration_sec: sec })}
              label={`Satz ${index + 1}`}
            />
          </div>
        )}

        {fields.distance && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.distance_m ?? 0}
              onChange={(val) => onChange(index, { ...set, distance_m: val })}
              min={0}
              max={99999}
              step={5}
              inputSize="sm"
              aria-label={`Satz ${index + 1} Distanz m`}
              incrementLabel="Distanz erhöhen"
              decrementLabel="Distanz verringern"
            />
          </div>
        )}

        {/* Status + Delete: inline ab sm */}
        <div className="hidden sm:block">
          <SetRowStatusControls
            index={index}
            set={set}
            onChange={onChange}
            onRemove={onRemove}
            canRemove={canRemove}
          />
        </div>
      </div>

      {/* Zeile 2 (nur Mobile): Status + Delete */}
      <div className="pl-8 sm:hidden">
        <SetRowStatusControls
          index={index}
          set={set}
          onChange={onChange}
          onRemove={onRemove}
          canRemove={canRemove}
        />
      </div>
    </div>
  );
}
