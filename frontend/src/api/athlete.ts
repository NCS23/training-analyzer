import { apiClient } from './client';

export interface KarvonenZone {
  zone: number;
  name: string;
  lower_bpm: number;
  upper_bpm: number;
  color: string;
  pct_min: number;
  pct_max: number;
}

export interface AthleteSettings {
  id: number;
  resting_hr: number | null;
  max_hr: number | null;
  karvonen_zones: KarvonenZone[] | null;
}

export async function getAthleteSettings(): Promise<AthleteSettings> {
  const response = await apiClient.get<AthleteSettings>('/api/v1/athlete/settings');
  return response.data;
}

export async function updateAthleteSettings(params: {
  resting_hr?: number;
  max_hr?: number;
}): Promise<AthleteSettings> {
  const response = await apiClient.put<AthleteSettings>('/api/v1/athlete/settings', params);
  return response.data;
}
