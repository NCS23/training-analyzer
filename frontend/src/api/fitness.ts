import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';

// ---------------------------------------------------------------------------
// Types — spiegeln die Backend-Pydantic-Schemas wider
// ---------------------------------------------------------------------------

export interface FormIndicatorResponse {
  status: 'fresh' | 'normal' | 'fatigued';
  label: string;
  color: 'green' | 'yellow' | 'orange';
  recommendation: string;
}

export interface ACWRResponse {
  ratio: number;
  zone: 'low' | 'optimal' | 'warning' | 'danger';
  message: string;
}

export interface FitnessScoreResponse {
  score: number;
  endurance_score: number;
  strength_score: number;
  trend: 'rising' | 'stable' | 'falling';
  trend_label: string;
  form: FormIndicatorResponse;
  acwr: ACWRResponse | null;
  context_message: string;
  updated_at: string;
}

export interface FitnessDataPoint {
  date: string;
  value: number;
}

export interface FitnessHistoryResponse {
  ctl_history: FitnessDataPoint[];
  atl_history: FitnessDataPoint[];
  tsb_history: FitnessDataPoint[];
  score_history: FitnessDataPoint[];
}

export interface InsightResponse {
  type: 'warning' | 'trend' | 'achievement' | 'recommendation' | 'info';
  priority: number;
  title: string;
  message: string;
  category: 'load' | 'balance' | 'performance' | 'plan' | 'recovery';
  icon: string;
}

export interface LastSessionSummary {
  id: number;
  date: string;
  workout_type: string;
  training_type: string | null;
  distance_km: number | null;
  duration_seconds: number | null;
  avg_pace_formatted: string | null;
  avg_heartrate: number | null;
  exercise_count: number | null;
  tonnage_kg: number | null;
  rpe: number | null;
  trimp_score: number | null;
  comparison_message: string;
}

export interface DayStatus {
  date: string;
  day_name: string;
  has_planned: boolean;
  has_completed: boolean;
  status: 'completed' | 'planned' | 'skipped' | 'extra' | 'rest';
}

export interface WeekProgressResponse {
  sessions_completed: number;
  sessions_planned: number;
  distance_completed_km: number;
  distance_planned_km: number | null;
  time_completed_seconds: number;
  time_planned_seconds: number | null;
  days: DayStatus[];
}

export interface NextSessionInfo {
  day_name: string;
  workout_type: 'running' | 'strength';
  description: string;
}

export interface GoalSummary {
  title: string;
  days_until: number;
  target_time_formatted: string | null;
}

export interface TodayResponse {
  greeting: string;
  motivation: string | null;
  fitness_score: FitnessScoreResponse;
  last_session: LastSessionSummary | null;
  week_progress: WeekProgressResponse;
  insights: InsightResponse[];
  next_session: NextSessionInfo | null;
  goal_summary: GoalSummary | null;
}

// ---------------------------------------------------------------------------
// API-Funktionen
// ---------------------------------------------------------------------------

export async function getToday(): Promise<TodayResponse> {
  const response = await apiClient.get<TodayResponse>('/api/v1/fitness/today');
  return response.data;
}

export async function getFitnessScore(): Promise<FitnessScoreResponse> {
  const response = await apiClient.get<FitnessScoreResponse>('/api/v1/fitness/score');
  return response.data;
}

export async function getFitnessHistory(days: number = 90): Promise<FitnessHistoryResponse> {
  const response = await apiClient.get<FitnessHistoryResponse>(
    `/api/v1/fitness/history?days=${days}`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// React Query Hooks
// ---------------------------------------------------------------------------

export function useToday() {
  return useQuery({
    queryKey: ['fitness', 'today'],
    queryFn: getToday,
    staleTime: 3 * 60 * 1000, // 3 Minuten — Dashboard täglich aktuell
  });
}

export function useFitnessHistory(days: number = 90) {
  return useQuery({
    queryKey: ['fitness', 'history', days],
    queryFn: () => getFitnessHistory(days),
    staleTime: 10 * 60 * 1000,
  });
}
