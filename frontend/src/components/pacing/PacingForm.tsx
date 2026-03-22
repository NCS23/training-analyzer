import { useState, useEffect } from 'react';
import { Button, Label, Select, Alert, AlertDescription } from '@nordlig/components';
import { Play } from 'lucide-react';
import type { RaceGoal } from '@/api/goals';
import type { ElevationSegment, PacingRequest, PacingRecommendationResponse } from '@/api/pacing';
import { DistanceTimeInputs } from './DistanceTimeInputs';
import { StrategyInputs } from './StrategyInputs';
import { WeatherInputs } from './WeatherInputs';

interface PacingFormProps {
  goals: RaceGoal[];
  loading: boolean;
  onGenerate: (params: PacingRequest) => void;
}

type Strategy = 'even' | 'negative' | 'effort_based';
type ElevationPreset = 'flat' | 'rolling' | 'hilly';

function usePacingForm(goals: RaceGoal[]) {
  const [goalId, setGoalId] = useState<number | null>(null);
  const [distance, setDistance] = useState('');
  const [timeH, setTimeH] = useState('');
  const [timeM, setTimeM] = useState('');
  const [timeS, setTimeS] = useState('');
  const [strategy, setStrategy] = useState<Strategy>('even');
  const [elevationPreset, setElevationPreset] = useState<ElevationPreset>('flat');
  const [temperature, setTemperature] = useState('');
  const [windSpeed, setWindSpeed] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [raceName, setRaceName] = useState('');
  const [elevationSegments, setElevationSegments] = useState<ElevationSegment[] | null>(null);

  useEffect(() => {
    if (!goalId) return;
    const goal = goals.find((g) => g.id === goalId);
    if (!goal) return;
    setDistance(String(goal.distance_km));
    setRaceName(goal.title);
    const secs = goal.target_time_seconds;
    setTimeH(String(Math.floor(secs / 3600)));
    setTimeM(String(Math.floor((secs % 3600) / 60)));
    setTimeS(String(secs % 60));
  }, [goalId, goals]);

  const getTimeSeconds = (): number => {
    const h = parseInt(timeH || '0', 10);
    const m = parseInt(timeM || '0', 10);
    const s = parseInt(timeS || '0', 10);
    return h * 3600 + m * 60 + s;
  };

  const validate = (): PacingRequest | null => {
    setError(null);
    const dist = parseFloat(distance);
    if (!dist || dist <= 0) {
      setError('Bitte eine gültige Distanz eingeben.');
      return null;
    }
    const totalSec = getTimeSeconds();
    if (totalSec <= 0) {
      setError('Bitte eine gültige Zielzeit eingeben.');
      return null;
    }
    const params: PacingRequest = {
      target_time_seconds: totalSec,
      distance_km: dist,
      strategy,
      elevation_preset: elevationSegments ? null : elevationPreset,
      elevation_segments: elevationSegments,
      goal_id: goalId,
    };
    const temp = parseFloat(temperature);
    if (!isNaN(temp)) params.temperature_celsius = temp;
    const wind = parseFloat(windSpeed);
    if (!isNaN(wind)) params.wind_speed_kmh = wind;
    return params;
  };

  return {
    goalId,
    setGoalId,
    distance,
    setDistance,
    timeH,
    setTimeH,
    timeM,
    setTimeM,
    timeS,
    setTimeS,
    strategy,
    setStrategy,
    elevationPreset,
    setElevationPreset,
    temperature,
    setTemperature,
    windSpeed,
    setWindSpeed,
    error,
    raceName,
    elevationSegments,
    setElevationSegments,
    getTimeSeconds,
    validate,
  };
}

export function PacingForm({ goals, loading, onGenerate }: PacingFormProps) {
  const form = usePacingForm(goals);
  const [reasoning, setReasoning] = useState<string | null>(null);
  const activeGoals = goals.filter((g) => g.is_active);
  const goalOptions = [
    { value: '', label: 'Manuell eingeben' },
    ...activeGoals.map((g) => ({
      value: String(g.id),
      label: `${g.title} — ${g.distance_km} km in ${g.target_time_formatted}`,
    })),
  ];

  const handleRecommendation = (rec: PacingRecommendationResponse) => {
    form.setStrategy(rec.strategy);
    form.setElevationPreset(rec.elevation_preset);
    setReasoning(rec.reasoning);
  };

  return (
    <div className="space-y-5">
      {activeGoals.length > 0 && (
        <div>
          <Label>Wettkampfziel</Label>
          <Select
            options={goalOptions}
            value={form.goalId ? String(form.goalId) : ''}
            onChange={(val) => form.setGoalId(val ? Number(val) : null)}
          />
        </div>
      )}

      <DistanceTimeInputs
        distance={form.distance}
        timeH={form.timeH}
        timeM={form.timeM}
        timeS={form.timeS}
        onDistanceChange={form.setDistance}
        onTimeHChange={form.setTimeH}
        onTimeMChange={form.setTimeM}
        onTimeSChange={form.setTimeS}
      />

      <StrategyInputs
        strategy={form.strategy}
        elevationPreset={form.elevationPreset}
        elevationSegments={form.elevationSegments}
        raceName={form.raceName}
        distanceKm={parseFloat(form.distance) || null}
        targetTimeSeconds={form.getTimeSeconds() || null}
        reasoning={reasoning}
        disabled={loading}
        onStrategyChange={form.setStrategy}
        onElevationChange={form.setElevationPreset}
        onElevationSegmentsChange={form.setElevationSegments}
        onRecommendation={handleRecommendation}
        onReasoningClose={() => setReasoning(null)}
      />

      <WeatherInputs
        temperature={form.temperature}
        windSpeed={form.windSpeed}
        onTemperatureChange={form.setTemperature}
        onWindSpeedChange={form.setWindSpeed}
      />

      {form.error && (
        <Alert variant="error">
          <AlertDescription>{form.error}</AlertDescription>
        </Alert>
      )}

      <Button
        variant="primary"
        onClick={() => {
          const p = form.validate();
          if (p) onGenerate(p);
        }}
        disabled={loading}
      >
        {loading ? (
          'Berechne…'
        ) : (
          <>
            <Play size={16} /> Strategie generieren
          </>
        )}
      </Button>
    </div>
  );
}
