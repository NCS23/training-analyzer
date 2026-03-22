import { Input, Label } from '@nordlig/components';
import { CloudSun } from 'lucide-react';

interface WeatherInputsProps {
  temperature: string;
  windSpeed: string;
  onTemperatureChange: (val: string) => void;
  onWindSpeedChange: (val: string) => void;
}

export function WeatherInputs({
  temperature,
  windSpeed,
  onTemperatureChange,
  onWindSpeedChange,
}: WeatherInputsProps) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1.5">
        <CloudSun size={14} className="text-[var(--color-text-muted)]" />
        <span className="text-sm font-medium text-[var(--color-text-muted)]">
          Wetter (optional)
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="temperature">Temperatur (°C)</Label>
          <Input
            id="temperature"
            type="number"
            inputSize="sm"
            value={temperature}
            onChange={(e) => onTemperatureChange(e.target.value)}
            placeholder="20"
          />
        </div>
        <div>
          <Label htmlFor="wind">Wind (km/h)</Label>
          <Input
            id="wind"
            type="number"
            inputSize="sm"
            value={windSpeed}
            onChange={(e) => onWindSpeedChange(e.target.value)}
            placeholder="10"
            min="0"
          />
        </div>
      </div>
    </div>
  );
}
