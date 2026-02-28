import { apiClient } from './client';

// --- Types ---

export interface ExerciseHistoryPoint {
  date: string;
  session_id: number;
  max_weight_kg: number;
  total_reps: number;
  total_sets: number;
  completed_sets: number;
  tonnage_kg: number;
  best_set_weight_kg: number;
  best_set_reps: number;
}

export interface ExerciseHistoryResponse {
  exercise_name: string;
  data_points: ExerciseHistoryPoint[];
  current_max_weight: number;
  previous_max_weight: number | null;
  weight_progression: number | null;
}

export interface PersonalRecord {
  exercise_name: string;
  record_type: 'max_weight' | 'max_volume_set' | 'max_tonnage_session';
  value: number;
  unit: string;
  date: string;
  session_id: number;
  detail?: string;
}

export interface PersonalRecordsResponse {
  records: PersonalRecord[];
  new_prs_session: PersonalRecord[] | null;
}

export interface WeeklyTonnagePoint {
  week: string;
  week_start: string;
  total_tonnage_kg: number;
  session_count: number;
  exercise_count: number;
}

export interface TonnageTrendResponse {
  weeks: WeeklyTonnagePoint[];
  total_tonnage_kg: number;
  avg_weekly_tonnage_kg: number;
  trend_direction: 'up' | 'down' | 'stable' | null;
}

export interface ExerciseListItem {
  name: string;
  category: string;
  session_count: number;
  last_date: string;
  last_max_weight_kg: number;
}

export interface ExerciseListResponse {
  exercises: ExerciseListItem[];
}

// --- API Functions ---

export async function getExerciseList(): Promise<ExerciseListResponse> {
  const response = await apiClient.get<ExerciseListResponse>('/api/v1/sessions/strength/exercises');
  return response.data;
}

export async function getExerciseProgression(
  exerciseName: string,
): Promise<ExerciseHistoryResponse> {
  const response = await apiClient.get<ExerciseHistoryResponse>(
    '/api/v1/sessions/strength/progression',
    { params: { exercise_name: exerciseName } },
  );
  return response.data;
}

export async function getPersonalRecords(sessionId?: number): Promise<PersonalRecordsResponse> {
  const response = await apiClient.get<PersonalRecordsResponse>('/api/v1/sessions/strength/prs', {
    params: sessionId != null ? { session_id: sessionId } : {},
  });
  return response.data;
}

export async function getTonnageTrend(days: number = 90): Promise<TonnageTrendResponse> {
  const response = await apiClient.get<TonnageTrendResponse>(
    '/api/v1/sessions/strength/tonnage-trend',
    { params: { days } },
  );
  return response.data;
}
