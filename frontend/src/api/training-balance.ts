import { apiClient } from './client';

// --- Types ---

export interface IntensityDistribution {
  easy_percent: number;
  moderate_percent: number;
  hard_percent: number;
  easy_sessions: number;
  moderate_sessions: number;
  hard_sessions: number;
  total_sessions: number;
  is_polarized: boolean;
}

export interface VolumeWeek {
  week: string;
  week_start: string;
  running_km: number;
  running_min: number;
  strength_sessions: number;
  total_sessions: number;
  volume_change_percent: number | null;
}

export interface MuscleGroupBalance {
  group: string;
  session_count: number;
  total_sets: number;
  percentage: number;
}

export interface SportMix {
  running_sessions: number;
  strength_sessions: number;
  running_percent: number;
  strength_percent: number;
  total_sessions: number;
}

export interface BalanceInsight {
  type: 'positive' | 'warning' | 'neutral';
  category: string;
  message: string;
}

export interface TrainingBalanceResponse {
  period_days: number;
  intensity: IntensityDistribution;
  volume_weeks: VolumeWeek[];
  muscle_groups: MuscleGroupBalance[];
  sport_mix: SportMix;
  insights: BalanceInsight[];
}

// --- API ---

export async function getTrainingBalance(
  days: number = 28,
): Promise<TrainingBalanceResponse> {
  const response = await apiClient.get<TrainingBalanceResponse>(
    `/api/v1/training-balance?days=${days}`,
  );
  return response.data;
}
