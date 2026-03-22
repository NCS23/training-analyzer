import { apiClient } from './client';

// ---------------------------------------------------------------------------
// Request Types
// ---------------------------------------------------------------------------

export interface ElevationSegment {
  km: number;
  gain_m: number;
  loss_m: number;
}

export interface PacingRequest {
  target_time_seconds: number;
  distance_km: number;
  strategy: 'even' | 'negative' | 'effort_based';
  elevation_preset?: 'flat' | 'rolling' | 'hilly' | null;
  elevation_segments?: ElevationSegment[] | null;
  temperature_celsius?: number | null;
  wind_speed_kmh?: number | null;
  humidity_percent?: number | null;
  goal_id?: number | null;
}

// ---------------------------------------------------------------------------
// Response Types
// ---------------------------------------------------------------------------

export interface KmPacingSplit {
  km: number;
  distance_km: number;
  target_pace_sec_per_km: number;
  target_pace_formatted: string;
  cumulative_seconds: number;
  cumulative_formatted: string;
  elevation_gain_m: number;
  elevation_loss_m: number;
  adjustment_note: string | null;
}

export interface WeatherAdjustment {
  temperature_celsius: number | null;
  wind_speed_kmh: number | null;
  humidity_percent: number | null;
  penalty_sec_per_km: number;
  description: string;
}

export interface PacingResponse {
  strategy: string;
  strategy_label: string;
  distance_km: number;
  target_time_seconds: number;
  target_time_formatted: string;
  avg_pace_sec_per_km: number;
  avg_pace_formatted: string;
  splits: KmPacingSplit[];
  weather_adjustment: WeatherAdjustment | null;
  notes: string[];
}

export interface RaceDayWeatherResponse {
  date: string;
  temperature_min: number;
  temperature_max: number;
  temperature_avg: number;
  wind_speed_max_kmh: number;
  wind_direction_deg: number | null;
  precipitation_mm: number;
  humidity_percent: number | null;
  weather_label: string;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export async function generatePacing(params: PacingRequest): Promise<PacingResponse> {
  const response = await apiClient.post<PacingResponse>('/api/v1/pacing/generate', params);
  return response.data;
}

export interface PacingRecommendationRequest {
  race_name?: string | null;
  distance_km: number;
  target_time_seconds: number;
  experience_level?: 'beginner' | 'intermediate' | 'advanced' | null;
}

export interface PacingRecommendationResponse {
  strategy: 'even' | 'negative' | 'effort_based';
  elevation_preset: 'flat' | 'rolling' | 'hilly';
  reasoning: string;
}

export async function getPacingRecommendation(
  params: PacingRecommendationRequest,
): Promise<PacingRecommendationResponse> {
  const response = await apiClient.post<PacingRecommendationResponse>(
    '/api/v1/pacing/recommend',
    params,
  );
  return response.data;
}

export async function parseGpxElevation(file: File): Promise<ElevationSegment[]> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<ElevationSegment[]>('/api/v1/pacing/parse-gpx', formData);
  return response.data;
}

export async function getWeatherForecast(
  lat: number,
  lng: number,
  date: string,
): Promise<RaceDayWeatherResponse> {
  const response = await apiClient.get<RaceDayWeatherResponse>('/api/v1/pacing/weather-forecast', {
    params: { lat, lng, date },
  });
  return response.data;
}
