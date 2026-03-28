import { useState, useEffect } from 'react';
import type { RaceGoal } from '@/api/goals';
import type { ElevationSegment, ExperienceLevel, PacingRequest } from '@/api/pacing';

export type Strategy = 'even' | 'negative' | 'effort_based';
export type ElevationPreset = 'flat' | 'rolling' | 'hilly';

const STRATEGIES: string[] = ['even', 'negative', 'effort_based'];
const PRESETS: string[] = ['flat', 'rolling', 'hilly'];

export interface SavedStrategyPrefill {
  strategy: string;
  elevation_preset: string | null;
  weather_adjustment: {
    temperature_celsius: number | null;
    wind_speed_kmh: number | null;
  } | null;
}

function applyPrefill(
  saved: SavedStrategyPrefill,
  setters: {
    setStrategy: (s: Strategy) => void;
    setElevationPreset: (p: ElevationPreset) => void;
    setTemperature: (t: string) => void;
    setWindSpeed: (w: string) => void;
  },
) {
  if (STRATEGIES.includes(saved.strategy)) {
    setters.setStrategy(saved.strategy as Strategy);
  }
  if (saved.elevation_preset && PRESETS.includes(saved.elevation_preset)) {
    setters.setElevationPreset(saved.elevation_preset as ElevationPreset);
  }
  const wa = saved.weather_adjustment;
  if (wa?.temperature_celsius != null) setters.setTemperature(String(wa.temperature_celsius));
  if (wa?.wind_speed_kmh != null) setters.setWindSpeed(String(wa.wind_speed_kmh));
}

export function usePacingForm(goals: RaceGoal[]) {
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
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>('intermediate');

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
    return (
      parseInt(timeH || '0', 10) * 3600 +
      parseInt(timeM || '0', 10) * 60 +
      parseInt(timeS || '0', 10)
    );
  };

  const validate = (): PacingRequest | null => {
    setError(null);
    const dist = parseFloat(distance);
    if (!dist || dist <= 0) return (setError('Bitte eine gültige Distanz eingeben.'), null);
    const totalSec = getTimeSeconds();
    if (totalSec <= 0) return (setError('Bitte eine gültige Zielzeit eingeben.'), null);
    const temp = parseFloat(temperature);
    const wind = parseFloat(windSpeed);
    return {
      target_time_seconds: totalSec,
      distance_km: dist,
      strategy,
      elevation_preset: elevationSegments ? null : elevationPreset,
      elevation_segments: elevationSegments,
      goal_id: goalId,
      ...(isNaN(temp) ? {} : { temperature_celsius: temp }),
      ...(isNaN(wind) ? {} : { wind_speed_kmh: wind }),
    };
  };

  const prefillFromStrategy = (saved: SavedStrategyPrefill) => {
    applyPrefill(saved, { setStrategy, setElevationPreset, setTemperature, setWindSpeed });
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
    experienceLevel,
    setExperienceLevel,
    getTimeSeconds,
    validate,
    prefillFromStrategy,
  };
}
