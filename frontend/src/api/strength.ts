import { apiClient } from './client';

// --- Types ---

export type ExerciseCategory = 'push' | 'pull' | 'legs' | 'core' | 'cardio' | 'drills';
export type SetStatus = 'completed' | 'reduced' | 'skipped';

export type SetType =
  | 'weight_reps'
  | 'bodyweight_reps'
  | 'weighted_bodyweight'
  | 'assisted_bodyweight'
  | 'duration'
  | 'weight_duration'
  | 'distance_duration'
  | 'weight_distance';

export const SET_TYPE_LABELS: Record<SetType, string> = {
  weight_reps: 'Gewicht + Wdh.',
  bodyweight_reps: 'Nur Wdh.',
  weighted_bodyweight: 'Zusatzgewicht',
  assisted_bodyweight: 'Assistiert',
  duration: 'Dauer',
  weight_duration: 'Gewicht + Dauer',
  distance_duration: 'Distanz + Dauer',
  weight_distance: 'Gewicht + Distanz',
};

export const SET_TYPE_OPTIONS: { value: SetType; label: string }[] = [
  { value: 'weight_reps', label: 'Gewicht + Wdh.' },
  { value: 'bodyweight_reps', label: 'Nur Wdh.' },
  { value: 'weighted_bodyweight', label: 'Zusatzgewicht + Wdh.' },
  { value: 'assisted_bodyweight', label: 'Assistiert + Wdh.' },
  { value: 'duration', label: 'Dauer' },
  { value: 'weight_duration', label: 'Gewicht + Dauer' },
  { value: 'distance_duration', label: 'Distanz (+ Dauer)' },
  { value: 'weight_distance', label: 'Gewicht + Distanz' },
];

/** Welche Felder pro Set-Typ angezeigt werden. */
export const SET_TYPE_FIELDS: Record<
  SetType,
  { reps: boolean; weight: boolean; duration: boolean; distance: boolean }
> = {
  weight_reps: { reps: true, weight: true, duration: false, distance: false },
  bodyweight_reps: { reps: true, weight: false, duration: false, distance: false },
  weighted_bodyweight: { reps: true, weight: true, duration: false, distance: false },
  assisted_bodyweight: { reps: true, weight: true, duration: false, distance: false },
  duration: { reps: false, weight: false, duration: true, distance: false },
  weight_duration: { reps: false, weight: true, duration: true, distance: false },
  distance_duration: { reps: false, weight: false, duration: true, distance: true },
  weight_distance: { reps: false, weight: true, duration: false, distance: true },
};

/** Typ-Gruppen für Metriken und Charts. */
export const WEIGHTED_TYPES: SetType[] = [
  'weight_reps',
  'weighted_bodyweight',
  'assisted_bodyweight',
  'weight_duration',
  'weight_distance',
];
export const REP_BASED_TYPES: SetType[] = ['bodyweight_reps'];
export const DURATION_TYPES: SetType[] = ['duration', 'weight_duration', 'distance_duration'];
export const DISTANCE_TYPES: SetType[] = ['distance_duration', 'weight_distance'];

export function isWeightedType(t: string): boolean {
  return WEIGHTED_TYPES.includes(t as SetType);
}
export function isRepBasedType(t: string): boolean {
  return REP_BASED_TYPES.includes(t as SetType);
}
export function isDurationType(t: string): boolean {
  return DURATION_TYPES.includes(t as SetType);
}
export function isDistanceType(t: string): boolean {
  return DISTANCE_TYPES.includes(t as SetType);
}

export interface SetInput {
  type?: SetType;
  reps?: number;
  weight_kg?: number;
  duration_sec?: number;
  distance_m?: number;
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
  plannedEntryId?: number;
}

export interface StrengthSessionCreateResponse {
  success: boolean;
  session_id: number;
  metrics: {
    total_exercises: number;
    total_sets: number;
    total_tonnage_kg: number;
    total_reps: number;
    total_duration_sec: number;
    total_distance_m: number;
    completed_sets: number;
  };
  file_data?: {
    has_file: boolean;
    hr_avg: number | null;
    hr_max: number | null;
    duration_sec: number | null;
  };
}

export interface LastCompleteSession {
  id: number;
  date: string;
  exercises: ExerciseInput[];
  total_tonnage_kg: number;
  duration_minutes: number | null;
}

export interface LastCompleteSessionResponse {
  found: boolean;
  session: LastCompleteSession | null;
}

export interface LastExerciseResponse {
  found: boolean;
  exercise: {
    exercise_name: string;
    category: string;
    sets: Array<{
      type?: string;
      reps?: number;
      weight_kg?: number;
      duration_sec?: number;
      distance_m?: number;
      status: string;
    }>;
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
  if (params.plannedEntryId != null) {
    formData.append('planned_entry_id', String(params.plannedEntryId));
  }

  const response = await apiClient.post<StrengthSessionCreateResponse>(
    '/api/v1/sessions/strength',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

export async function getLastCompleteStrengthSession(): Promise<LastCompleteSessionResponse> {
  const response = await apiClient.get<LastCompleteSessionResponse>(
    '/api/v1/sessions/strength/last-complete',
  );
  return response.data;
}

export interface UpdateExercisesResponse {
  success: boolean;
  session_id: number;
  exercises: Array<{
    name: string;
    category: string;
    sets: Array<{
      type?: string;
      reps?: number;
      weight_kg?: number;
      duration_sec?: number;
      distance_m?: number;
      status: string;
    }>;
  }>;
  metrics: {
    total_exercises: number;
    total_sets: number;
    total_tonnage_kg: number;
    total_reps: number;
    total_duration_sec: number;
    total_distance_m: number;
    completed_sets: number;
  };
}

export async function updateStrengthExercises(
  sessionId: number,
  exercises: ExerciseInput[],
): Promise<UpdateExercisesResponse> {
  const formData = new FormData();
  formData.append('exercises_json', JSON.stringify(exercises));
  const response = await apiClient.patch<UpdateExercisesResponse>(
    `/api/v1/sessions/strength/${sessionId}/exercises`,
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
