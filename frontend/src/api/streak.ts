import { apiClient } from './client';

export interface StreakResponse {
  current_streak: number;
  longest_streak: number;
  last_training_date: string | null;
  streak_at_risk: boolean;
  calendar: Record<string, number>; // { "YYYY-MM-DD": session_count }
}

export async function getStreak(): Promise<StreakResponse> {
  const response = await apiClient.get<StreakResponse>('/api/v1/streak');
  return response.data;
}
