/**
 * PacingPanel — Pacing-Berechnung für Routensegmente (#548).
 *
 * Strategie wählen, Zielzeit eingeben, optional Wetter.
 * Berechnet Pace-Ziele und füllt Segmente automatisch.
 */

import {
  Button,
  Card,
  CardBody,
  Input,
  Select,
  Spinner,
  Alert,
  AlertDescription,
  useToast,
} from '@nordlig/components';
import { Zap, CloudRain, ChevronDown, ChevronUp } from 'lucide-react';
import type { RoutePacingResponse, RouteSegment } from '@/api/routes';
import { useRoutePacing } from '@/hooks/useRoutePacing';

// ---------------------------------------------------------------------------
// Types & Constants
// ---------------------------------------------------------------------------

interface PacingPanelProps {
  routeId: number | null;
  distanceKm: number;
  segments: RouteSegment[];
  onSegmentsUpdate: (segments: RouteSegment[]) => void;
}

type Strategy = 'even' | 'negative' | 'effort_based';

const STRATEGY_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'even', label: 'Gleichmäßig' },
  { value: 'negative', label: 'Negative Splits' },
  { value: 'effort_based', label: 'Effort-Based (Höhenangepasst)' },
];

// ---------------------------------------------------------------------------
// Sub-Components
// ---------------------------------------------------------------------------

function WeatherToggle({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors"
      onClick={onToggle}
    >
      <CloudRain className="w-3.5 h-3.5" />
      Wetter-Anpassung
      {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
    </button>
  );
}

function WeatherInputs({
  temperature,
  windSpeed,
  humidity,
  onTemperature,
  onWindSpeed,
  onHumidity,
}: {
  temperature: string;
  windSpeed: string;
  humidity: string;
  onTemperature: (v: string) => void;
  onWindSpeed: (v: string) => void;
  onHumidity: (v: string) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <div className="space-y-1">
        <label className="text-xs text-[var(--color-text-muted)]">Temperatur °C</label>
        <Input
          type="number"
          placeholder="z.B. 25"
          value={temperature}
          onChange={(e) => onTemperature(e.target.value)}
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-[var(--color-text-muted)]">Wind km/h</label>
        <Input
          type="number"
          placeholder="z.B. 15"
          value={windSpeed}
          onChange={(e) => onWindSpeed(e.target.value)}
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs text-[var(--color-text-muted)]">Feuchte %</label>
        <Input
          type="number"
          placeholder="z.B. 70"
          value={humidity}
          onChange={(e) => onHumidity(e.target.value)}
        />
      </div>
    </div>
  );
}

function PacingNotes({ result }: { result: RoutePacingResponse }) {
  return (
    <>
      {result.general_notes.length > 0 && (
        <Alert variant="info">
          <AlertDescription>
            {result.general_notes.map((note, i) => (
              <span key={i} className="block text-xs">
                {note}
              </span>
            ))}
          </AlertDescription>
        </Alert>
      )}
      {result.weather_notes && (
        <Alert variant="warning">
          <AlertDescription className="text-xs">🌡️ {result.weather_notes}</AlertDescription>
        </Alert>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function PacingPanel({ routeId, distanceKm, segments, onSegmentsUpdate }: PacingPanelProps) {
  const { toast } = useToast();
  const pacing = useRoutePacing();

  if (!routeId || segments.length === 0) return null;

  const handleCalculate = async () => {
    try {
      const updated = await pacing.calculate(routeId, segments);
      onSegmentsUpdate(updated);
      toast({ title: 'Pacing berechnet', variant: 'success' });
    } catch {
      toast({ title: 'Pacing-Berechnung fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <Card>
      <CardBody className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-[var(--color-text-base)]">Pacing berechnen</h3>
          {pacing.result && (
            <span className="text-xs text-[var(--color-text-muted)]">
              ⌀ {pacing.result.avg_pace_formatted}/km → {pacing.result.target_time_formatted}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs text-[var(--color-text-muted)]">Strategie</label>
            <Select
              options={STRATEGY_OPTIONS}
              value={pacing.strategy}
              onChange={(val) => {
                if (val) pacing.setStrategy(val as Strategy);
              }}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[var(--color-text-muted)]">
              Zielzeit ({distanceKm.toFixed(1)} km)
            </label>
            <Input
              placeholder="z.B. 55:00 oder 1:50:00"
              value={pacing.targetTimeInput}
              onChange={(e) => pacing.setTargetTimeInput(e.target.value)}
            />
          </div>
        </div>

        <WeatherToggle
          open={pacing.showWeather}
          onToggle={() => pacing.setShowWeather(!pacing.showWeather)}
        />
        {pacing.showWeather && (
          <WeatherInputs
            temperature={pacing.weather.temperature}
            windSpeed={pacing.weather.windSpeed}
            humidity={pacing.weather.humidity}
            onTemperature={pacing.setTemperature}
            onWindSpeed={pacing.setWindSpeed}
            onHumidity={pacing.setHumidity}
          />
        )}

        <Button
          variant="primary"
          size="sm"
          onClick={handleCalculate}
          disabled={!pacing.canCalculate || pacing.loading}
          className="w-full sm:w-auto"
        >
          {pacing.loading ? (
            <Spinner size="sm" />
          ) : (
            <>
              <Zap className="w-4 h-4 mr-1.5" />
              Pacing berechnen
            </>
          )}
        </Button>

        {pacing.result && <PacingNotes result={pacing.result} />}
      </CardBody>
    </Card>
  );
}
