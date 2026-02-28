import { apiClient } from './client';

// --- Types ---

export type ExerciseCategory = 'push' | 'pull' | 'legs' | 'core' | 'cardio';
export type SetStatus = 'completed' | 'reduced' | 'skipped';

export interface SetInput {
  reps: number;
  weight_kg: number;
  status: SetStatus;
}

export interface ExerciseInput {
  name: string;
  category: ExerciseCategory;
  sets: SetInput[];
}

export interface StrengthSessionCreateParams {
  date: string; // YYYY-MM-DD
  duration_minutes: number;
  exercises: ExerciseInput[];
  notes?: string;
  rpe?: number;
  trainingFile?: File;
}

export interface StrengthSessionCreateResponse {
  success: boolean;
  session_id: number;
  metrics: {
    total_exercises: number;
    total_sets: number;
    total_tonnage_kg: number;
    completed_sets: number;
  };
  file_data?: {
    has_file: boolean;
    hr_avg: number | null;
    hr_max: number | null;
    duration_sec: number | null;
  };
}

export interface LastExerciseResponse {
  found: boolean;
  exercise: {
    exercise_name: string;
    category: string;
    sets: Array<{ reps: number; weight_kg: number; status: string }>;
    session_date: string;
  } | null;
}

// --- API Functions ---

export async function createStrengthSession(
  params: StrengthSessionCreateParams,
): Promise<StrengthSessionCreateResponse> {
  const formData = new FormData();
  formData.append('exercises_json', JSON.stringify(params.exercises));
  formData.append('training_date', params.date);
  formData.append('duration_minutes', String(params.duration_minutes));

  if (params.notes) {
    formData.append('notes', params.notes);
  }
  if (params.rpe != null) {
    formData.append('rpe', String(params.rpe));
  }
  if (params.trainingFile) {
    formData.append('training_file', params.trainingFile);
  }

  const response = await apiClient.post<StrengthSessionCreateResponse>(
    '/api/v1/sessions/strength',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

export async function getLastExerciseSets(exerciseName: string): Promise<LastExerciseResponse> {
  const response = await apiClient.get<LastExerciseResponse>(
    '/api/v1/sessions/strength/last-exercises',
    { params: { exercise_name: exerciseName } },
  );
  return response.data;
}
