/**
 * Hook für Route-Pacing-Berechnung (#548).
 * Kapselt State und API-Call für die Pacing-Integration.
 */

import { useState, useCallback } from 'react';
import type { RoutePacingResponse, RouteSegment } from '@/api/routes';
import { calculateRoutePacing } from '@/api/routes';

type Strategy = 'even' | 'negative' | 'effort_based';

interface WeatherState {
  temperature: string;
  windSpeed: string;
  humidity: string;
}

export interface UseRoutePacingReturn {
  strategy: Strategy;
  setStrategy: (s: Strategy) => void;
  targetTimeInput: string;
  setTargetTimeInput: (v: string) => void;
  showWeather: boolean;
  setShowWeather: (v: boolean) => void;
  weather: WeatherState;
  setTemperature: (v: string) => void;
  setWindSpeed: (v: string) => void;
  setHumidity: (v: string) => void;
  loading: boolean;
  result: RoutePacingResponse | null;
  canCalculate: boolean;
  calculate: (routeId: number, segments: RouteSegment[]) => Promise<RouteSegment[]>;
}

function parseTimeInput(value: string): number | null {
  const parts = value.split(':').map(Number);
  if (parts.some(isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return null;
}

export function useRoutePacing(): UseRoutePacingReturn {
  const [strategy, setStrategy] = useState<Strategy>('even');
  const [targetTimeInput, setTargetTimeInput] = useState('');
  const [showWeather, setShowWeather] = useState(false);
  const [temperature, setTemperature] = useState('');
  const [windSpeed, setWindSpeed] = useState('');
  const [humidity, setHumidity] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RoutePacingResponse | null>(null);

  const targetTimeSeconds = parseTimeInput(targetTimeInput);
  const canCalculate = !!(targetTimeSeconds && targetTimeSeconds > 0);

  const calculate = useCallback(
    async (routeId: number, segments: RouteSegment[]): Promise<RouteSegment[]> => {
      if (!targetTimeSeconds) return segments;
      setLoading(true);
      try {
        const response = await calculateRoutePacing(routeId, {
          target_time_seconds: targetTimeSeconds,
          strategy,
          temperature_celsius: temperature ? Number(temperature) : null,
          wind_speed_kmh: windSpeed ? Number(windSpeed) : null,
          humidity_percent: humidity ? Number(humidity) : null,
        });
        setResult(response);
        return segments.map((seg, idx) => {
          const p = response.segment_pacing.find((sp) => sp.segment_index === idx);
          return p
            ? { ...seg, target_pace_min: p.target_pace_min, target_pace_max: p.target_pace_max }
            : seg;
        });
      } finally {
        setLoading(false);
      }
    },
    [targetTimeSeconds, strategy, temperature, windSpeed, humidity],
  );

  return {
    strategy,
    setStrategy,
    targetTimeInput,
    setTargetTimeInput,
    showWeather,
    setShowWeather,
    weather: { temperature, windSpeed, humidity },
    setTemperature,
    setWindSpeed,
    setHumidity,
    loading,
    result,
    canCalculate,
    calculate,
  };
}
