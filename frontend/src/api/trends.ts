import { apiClient } from './client';

export interface WeeklyDataPoint {
  week: string;
  week_start: string;
  session_count: number;
  total_distance_km: number;
  total_duration_sec: number;
  avg_pace_sec_per_km: number | null;
  avg_pace_formatted: string | null;
  avg_hr_bpm: number | null;
}

export interface TrendInsight {
  type: 'positive' | 'warning' | 'neutral';
  message: string;
}

export interface TrendResponse {
  weeks: WeeklyDataPoint[];
  insights: TrendInsight[];
}

export async function getTrends(days: number = 28): Promise<TrendResponse> {
  const response = await apiClient.get<TrendResponse>(`/api/v1/trends?days=${days}`);
  return response.data;
}

// --- Weather Correlation (#369) ---

export interface WeatherCorrelationPoint {
  date: string;
  pace_sec_per_km: number;
  temperature_c: number;
  wind_speed_kmh: number;
  precipitation_mm: number;
  weather_label: string;
  aqi: number | null;
}

export interface WeatherCorrelationResponse {
  data_points: WeatherCorrelationPoint[];
  insights: TrendInsight[];
  avg_pace_by_condition: Record<string, number>;
}

export async function getWeatherCorrelation(
  days: number = 90,
): Promise<WeatherCorrelationResponse> {
  const response = await apiClient.get<WeatherCorrelationResponse>(
    `/api/v1/trends/weather-correlation?days=${days}`,
  );
  return response.data;
}
