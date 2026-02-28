import { apiClient } from './client';

// --- Types ---

export interface RunInterval {
  type: 'work' | 'rest' | 'warmup' | 'cooldown';
  duration_minutes: number;
  target_pace_min: string | null;
  target_pace_max: string | null;
  target_hr_min: number | null;
  target_hr_max: number | null;
  repeats: number;
}

export interface RunDetails {
  run_type: 'recovery' | 'easy' | 'long_run' | 'tempo' | 'intervals';
  target_duration_minutes: number | null;
  target_pace_min: string | null;
  target_pace_max: string | null;
  target_hr_min: number | null;
  target_hr_max: number | null;
  intervals: RunInterval[] | null;
}

export interface WeeklyPlanEntry {
  day_of_week: number; // 0=Mon, 6=Sun
  training_type: string | null; // 'strength' | 'running' | null
  plan_id: number | null;
  plan_name: string | null;
  is_rest_day: boolean;
  notes: string | null;
  run_details: RunDetails | null;
}

export interface WeeklyPlanResponse {
  week_start: string; // YYYY-MM-DD
  entries: WeeklyPlanEntry[];
}

export interface WeeklyPlanSaveEntry {
  day_of_week: number;
  training_type?: string | null;
  plan_id?: number | null;
  is_rest_day: boolean;
  notes?: string | null;
  run_details?: RunDetails | null;
}

export interface WeeklyPlanSaveRequest {
  week_start: string;
  entries: WeeklyPlanSaveEntry[];
}

// --- API Functions ---

export async function getWeeklyPlan(
  weekStart?: string,
): Promise<WeeklyPlanResponse> {
  const params = new URLSearchParams();
  if (weekStart) params.set('week_start', weekStart);

  const url = params.toString()
    ? `/api/v1/weekly-plan?${params.toString()}`
    : '/api/v1/weekly-plan';

  const response = await apiClient.get<WeeklyPlanResponse>(url);
  return response.data;
}

export async function saveWeeklyPlan(
  data: WeeklyPlanSaveRequest,
): Promise<WeeklyPlanResponse> {
  const response = await apiClient.put<WeeklyPlanResponse>(
    '/api/v1/weekly-plan',
    data,
  );
  return response.data;
}

export async function clearWeeklyPlan(
  weekStart?: string,
): Promise<{ success: boolean }> {
  const params = new URLSearchParams();
  if (weekStart) params.set('week_start', weekStart);

  const url = params.toString()
    ? `/api/v1/weekly-plan?${params.toString()}`
    : '/api/v1/weekly-plan';

  const response = await apiClient.delete<{ success: boolean }>(url);
  return response.data;
}
