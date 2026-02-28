import { apiClient } from './client';

export interface Exercise {
  id: number;
  name: string;
  category: string;
  is_favorite: boolean;
  is_custom: boolean;
  usage_count: number;
  last_used_at: string | null;

  // Enrichment fields
  instructions: string[] | null;
  primary_muscles: string[] | null;
  secondary_muscles: string[] | null;
  image_urls: string[] | null;
  equipment: string | null;
  level: string | null;
  force: string | null;
  mechanic: string | null;
  exercise_db_id: string | null;
}

export interface ExerciseListResponse {
  exercises: Exercise[];
  total: number;
}

export interface ExerciseFilters {
  category?: string;
  search?: string;
  favoritesOnly?: boolean;
}

export async function listExercises(filters?: ExerciseFilters): Promise<ExerciseListResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.set('category', filters.category);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.favoritesOnly) params.set('favorites_only', 'true');

  const url = `/api/v1/exercises${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await apiClient.get<ExerciseListResponse>(url);
  return response.data;
}

export async function getExercise(exerciseId: number): Promise<Exercise> {
  const response = await apiClient.get<Exercise>(`/api/v1/exercises/${exerciseId}`);
  return response.data;
}

export async function createExercise(params: {
  name: string;
  category: string;
}): Promise<Exercise> {
  const response = await apiClient.post<Exercise>('/api/v1/exercises', params);
  return response.data;
}

export async function updateExercise(
  exerciseId: number,
  params: {
    name?: string;
    category?: string;
    is_favorite?: boolean;
    instructions?: string[];
    primary_muscles?: string[];
    secondary_muscles?: string[];
  },
): Promise<Exercise> {
  const response = await apiClient.patch<Exercise>(`/api/v1/exercises/${exerciseId}`, params);
  return response.data;
}

export async function toggleFavorite(exerciseId: number): Promise<Exercise> {
  const response = await apiClient.patch<Exercise>(`/api/v1/exercises/${exerciseId}/favorite`);
  return response.data;
}

export async function deleteExercise(exerciseId: number): Promise<void> {
  await apiClient.delete(`/api/v1/exercises/${exerciseId}`);
}

export async function enrichExercise(
  exerciseId: number,
  exerciseDbId?: string,
): Promise<Exercise> {
  const body = exerciseDbId ? { exercise_db_id: exerciseDbId } : undefined;
  const response = await apiClient.post<Exercise>(
    `/api/v1/exercises/${exerciseId}/enrich`,
    body,
  );
  return response.data;
}

// --- Exercise DB Search (free-exercise-db, 873 exercises) ---

export interface ExerciseDbEntry {
  id: string;
  name: string;
  name_de: string | null;
  category: string | null;
  equipment: string | null;
  primary_muscles: string[];
  level: string | null;
  force: string | null;
}

export interface ExerciseDbSearchResponse {
  exercises: ExerciseDbEntry[];
  total: number;
}

export interface ExerciseDbSearchParams {
  q?: string;
  muscle?: string;
  equipment?: string;
  limit?: number;
  offset?: number;
}

export async function searchExerciseDb(
  params?: ExerciseDbSearchParams,
): Promise<ExerciseDbSearchResponse> {
  const urlParams = new URLSearchParams();
  if (params?.q) urlParams.set('q', params.q);
  if (params?.muscle) urlParams.set('muscle', params.muscle);
  if (params?.equipment) urlParams.set('equipment', params.equipment);
  if (params?.limit) urlParams.set('limit', String(params.limit));
  if (params?.offset) urlParams.set('offset', String(params.offset));

  const qs = urlParams.toString();
  const url = `/api/v1/exercises/exercise-db/search${qs ? `?${qs}` : ''}`;
  const response = await apiClient.get<ExerciseDbSearchResponse>(url);
  return response.data;
}
