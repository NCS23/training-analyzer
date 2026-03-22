import { Input, Label } from '@nordlig/components';

interface DistanceTimeInputsProps {
  distance: string;
  timeH: string;
  timeM: string;
  timeS: string;
  onDistanceChange: (val: string) => void;
  onTimeHChange: (val: string) => void;
  onTimeMChange: (val: string) => void;
  onTimeSChange: (val: string) => void;
}

export function DistanceTimeInputs({
  distance,
  timeH,
  timeM,
  timeS,
  onDistanceChange,
  onTimeHChange,
  onTimeMChange,
  onTimeSChange,
}: DistanceTimeInputsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <Label htmlFor="distance">Distanz (km)</Label>
        <Input
          id="distance"
          type="number"
          inputSize="sm"
          value={distance}
          onChange={(e) => onDistanceChange(e.target.value)}
          placeholder="21.1"
          min="0.1"
          step="0.1"
        />
      </div>
      <div>
        <Label>Zielzeit</Label>
        <div className="grid grid-cols-3 gap-2">
          <Input
            inputSize="sm"
            type="number"
            value={timeH}
            onChange={(e) => onTimeHChange(e.target.value)}
            placeholder="Std"
            min="0"
          />
          <Input
            inputSize="sm"
            type="number"
            value={timeM}
            onChange={(e) => onTimeMChange(e.target.value)}
            placeholder="Min"
            min="0"
            max="59"
          />
          <Input
            inputSize="sm"
            type="number"
            value={timeS}
            onChange={(e) => onTimeSChange(e.target.value)}
            placeholder="Sek"
            min="0"
            max="59"
          />
        </div>
      </div>
    </div>
  );
}
