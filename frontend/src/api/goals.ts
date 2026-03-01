import { apiClient } from './client';

export interface TrainingPlanSummaryForGoal {
  id: number;
  name: string;
  status: string;
}

export interface RaceGoal {
  id: number;
  title: string;
  race_date: string;
  distance_km: number;
  target_time_seconds: number;
  target_time_formatted: string;
  target_pace_formatted: string;
  is_active: boolean;
  days_until: number;
  training_plan_id: number | null;
  training_plan_summary: TrainingPlanSummaryForGoal | null;
  created_at: string;
  updated_at: string;
}

export interface RaceGoalListResponse {
  goals: RaceGoal[];
}

export interface RaceGoalCreateParams {
  title: string;
  race_date: string;
  distance_km: number;
  target_time_seconds: number;
}

export interface RaceGoalUpdateParams {
  title?: string;
  race_date?: string;
  distance_km?: number;
  target_time_seconds?: number;
  is_active?: boolean;
}

export async function listGoals(): Promise<RaceGoalListResponse> {
  const response = await apiClient.get<RaceGoalListResponse>('/api/v1/goals');
  return response.data;
}

export async function createGoal(params: RaceGoalCreateParams): Promise<RaceGoal> {
  const response = await apiClient.post<RaceGoal>('/api/v1/goals', params);
  return response.data;
}

export async function updateGoal(goalId: number, params: RaceGoalUpdateParams): Promise<RaceGoal> {
  const response = await apiClient.patch<RaceGoal>(`/api/v1/goals/${goalId}`, params);
  return response.data;
}

export async function deleteGoal(goalId: number): Promise<void> {
  await apiClient.delete(`/api/v1/goals/${goalId}`);
}

export interface GoalProgress {
  goal: RaceGoal;
  current_pace_sec_per_km: number | null;
  current_pace_formatted: string | null;
  target_pace_sec_per_km: number;
  target_pace_formatted: string;
  pace_gap_sec: number | null;
  pace_gap_formatted: string | null;
  pace_gap_label: string | null;
  progress_percent: number | null;
  sessions_used: number;
  estimated_finish_seconds: number | null;
  estimated_finish_formatted: string | null;
  finish_delta_seconds: number | null;
  finish_delta_formatted: string | null;
  finish_delta_label: string | null;
  weekly_pace_trend_sec: number | null;
  weekly_pace_trend_label: string | null;
  weeks_to_goal: number | null;
  goal_reachable: boolean | null;
}

export async function getGoalProgress(goalId: number): Promise<GoalProgress> {
  const response = await apiClient.get<GoalProgress>(`/api/v1/goals/${goalId}/progress`);
  return response.data;
}
