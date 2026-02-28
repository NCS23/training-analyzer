import { apiClient } from './client';

// --- Types ---

export type ExerciseType = 'kraft' | 'mobilitaet' | 'dehnung';
export type ExerciseCategory = 'push' | 'pull' | 'legs' | 'core' | 'cardio';

export interface PlanExercise {
  name: string;
  category: ExerciseCategory;
  sets: number;
  reps: number;
  weight_kg: number | null;
  exercise_type: ExerciseType;
  notes: string | null;
}

export interface TrainingPlan {
  id: number;
  name: string;
  description: string | null;
  session_type: string;
  exercises: PlanExercise[];
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingPlanSummary {
  id: number;
  name: string;
  session_type: string;
  exercise_count: number;
  total_sets: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingPlanListResponse {
  plans: TrainingPlanSummary[];
  total: number;
}

export interface TrainingPlanCreateParams {
  name: string;
  description?: string;
  session_type: string;
  exercises: PlanExercise[];
}

export interface TrainingPlanUpdateParams {
  name?: string;
  description?: string;
  exercises?: PlanExercise[];
}

// --- API Functions ---

export async function listTrainingPlans(
  sessionType?: string,
): Promise<TrainingPlanListResponse> {
  const params = new URLSearchParams();
  if (sessionType) params.set('session_type', sessionType);

  const url = params.toString()
    ? `/api/v1/plans?${params.toString()}`
    : '/api/v1/plans';

  const response = await apiClient.get<TrainingPlanListResponse>(url);
  return response.data;
}

export async function getTrainingPlan(planId: number): Promise<TrainingPlan> {
  const response = await apiClient.get<TrainingPlan>(`/api/v1/plans/${planId}`);
  return response.data;
}

export async function createTrainingPlan(
  params: TrainingPlanCreateParams,
): Promise<TrainingPlan> {
  const response = await apiClient.post<TrainingPlan>('/api/v1/plans', params);
  return response.data;
}

export async function updateTrainingPlan(
  planId: number,
  params: TrainingPlanUpdateParams,
): Promise<TrainingPlan> {
  const response = await apiClient.patch<TrainingPlan>(
    `/api/v1/plans/${planId}`,
    params,
  );
  return response.data;
}

export async function deleteTrainingPlan(planId: number): Promise<void> {
  await apiClient.delete(`/api/v1/plans/${planId}`);
}

export async function duplicateTrainingPlan(
  planId: number,
): Promise<TrainingPlan> {
  const response = await apiClient.post<TrainingPlan>(
    `/api/v1/plans/${planId}/duplicate`,
  );
  return response.data;
}
