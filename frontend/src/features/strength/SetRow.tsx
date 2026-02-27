import { NumberInput, Select, Button } from '@nordlig/components';
import { Trash2 } from 'lucide-react';
import type { SetInput, SetStatus } from '@/api/strength';

const statusOptions = [
  { value: 'completed', label: 'Fertig' },
  { value: 'reduced', label: 'Reduziert' },
  { value: 'skipped', label: 'Ausgelassen' },
];

interface SetRowProps {
  index: number;
  set: SetInput;
  onChange: (index: number, set: SetInput) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}

export function SetRow({ index, set, onChange, onRemove, canRemove }: SetRowProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--color-text-muted)] w-6 shrink-0 text-center tabular-nums">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        <NumberInput
          value={set.reps}
          onChange={(val) => onChange(index, { ...set, reps: val })}
          min={0}
          max={999}
          step={1}
          inputSize="sm"
          aria-label={`Satz ${index + 1} Wiederholungen`}
          incrementLabel="Wiederholung hinzufuegen"
          decrementLabel="Wiederholung entfernen"
        />
      </div>
      <div className="flex-1 min-w-0">
        <NumberInput
          value={set.weight_kg}
          onChange={(val) => onChange(index, { ...set, weight_kg: val })}
          min={0}
          max={999}
          step={2.5}
          inputSize="sm"
          aria-label={`Satz ${index + 1} Gewicht kg`}
          incrementLabel="Gewicht erhoehen"
          decrementLabel="Gewicht verringern"
        />
      </div>
      <div className="w-28 shrink-0">
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
