import { useState, useEffect } from 'react';
import { Button, Alert, AlertDescription } from '@nordlig/components';
import { Play } from 'lucide-react';
import type { RaceGoal } from '@/api/goals';
import type { PacingRequest, PacingRecommendationResponse } from '@/api/pacing';
import { usePacingForm } from './usePacingForm';
import type { SavedStrategyPrefill } from './usePacingForm';
import { GoalSelector } from './GoalSelector';
import { DistanceTimeInputs } from './DistanceTimeInputs';
import { StrategyInputs } from './StrategyInputs';
import { WeatherInputs } from './WeatherInputs';

export type { SavedStrategyPrefill } from './usePacingForm';

interface PacingFormProps {
  goals: RaceGoal[];
  loading: boolean;
  onGenerate: (params: PacingRequest) => void;
  onGoalChange?: (goalId: number | null) => void;
  savedStrategyPrefill?: SavedStrategyPrefill | null;
}

export function PacingForm({
  goals,
  loading,
  onGenerate,
  onGoalChange,
  savedStrategyPrefill,
}: PacingFormProps) {
  const form = usePacingForm(goals);
  const [reasoning, setReasoning] = useState<string | null>(null);

  useEffect(() => {
    if (savedStrategyPrefill) form.prefillFromStrategy(savedStrategyPrefill);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedStrategyPrefill]);

  const handleGoalChange = (val: string | undefined) => {
    const id = val ? Number(val) : null;
    form.setGoalId(id);
    onGoalChange?.(id);
  };

  const handleRecommendation = (rec: PacingRecommendationResponse) => {
    form.setStrategy(rec.strategy);
    if (rec.elevation_preset) form.setElevationPreset(rec.elevation_preset);
    setReasoning(rec.reasoning);
  };

  return (
    <div className="space-y-5">
      <GoalSelector goals={goals} goalId={form.goalId} onChange={handleGoalChange} />

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

      <WeatherInputs
        temperature={form.temperature}
        windSpeed={form.windSpeed}
        onTemperatureChange={form.setTemperature}
        onWindSpeedChange={form.setWindSpeed}
      />

      <StrategyInputs
        strategy={form.strategy}
        elevationPreset={form.elevationPreset}
        elevationSegments={form.elevationSegments}
        experienceLevel={form.experienceLevel}
        raceName={form.raceName}
        distanceKm={parseFloat(form.distance) || null}
        targetTimeSeconds={form.getTimeSeconds() || null}
        temperatureCelsius={parseFloat(form.temperature) || null}
        reasoning={reasoning}
        disabled={loading}
        onStrategyChange={form.setStrategy}
        onElevationChange={form.setElevationPreset}
        onElevationSegmentsChange={form.setElevationSegments}
        onExperienceLevelChange={form.setExperienceLevel}
        onRecommendation={handleRecommendation}
        onReasoningClose={() => setReasoning(null)}
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
        className="w-full"
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
