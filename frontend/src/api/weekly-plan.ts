import { apiClient } from './client';
import type { Segment } from './segment';
import type { TemplateExercise } from './session-templates';

// --- Types ---

export interface RunInterval {
  type: 'warmup' | 'cooldown' | 'steady' | 'work' | 'recovery_jog' | 'rest' | 'strides' | 'drills';
  duration_minutes?: number | null;
  distance_km?: number | null;
  target_pace_min: string | null;
  target_pace_max: string | null;
  target_hr_min: number | null;
  target_hr_max: number | null;
  repeats: number;
  notes?: string | null;
  exercise_name?: string | null;
}

export interface RunDetails {
  run_type:
    | 'recovery'
    | 'easy'
    | 'long_run'
    | 'progression'
    | 'tempo'
    | 'intervals'
    | 'repetitions'
    | 'fartlek'
    | 'race';
  target_duration_minutes: number | null;
  target_pace_min: string | null;
  target_pace_max: string | null;
  target_hr_min: number | null;
  target_hr_max: number | null;
  intervals: RunInterval[] | null;
  segments: Segment[];
}

export interface PlannedSession {
  id?: number;
  position: number;
  training_type: string; // 'strength' | 'running'
  template_id?: number | null;
  template_name?: string | null;
  notes?: string | null;
  run_details?: RunDetails | null;
  exercises?: TemplateExercise[] | null;
  status?: 'active' | 'skipped'; // default: 'active'
}

export interface WeeklyPlanEntry {
  day_of_week: number; // 0=Mon, 6=Sun
  sessions: PlannedSession[];
  is_rest_day: boolean;
  notes: string | null;
  plan_id: number | null;
  edited: boolean;
}

export interface WeeklyPlanResponse {
  week_start: string; // YYYY-MM-DD
  entries: WeeklyPlanEntry[];
}

export interface WeeklyPlanSaveEntry {
  day_of_week: number;
  is_rest_day: boolean;
  notes?: string | null;
  sessions: PlannedSession[];
}

export interface WeeklyPlanSaveRequest {
  week_start: string;
  entries: WeeklyPlanSaveEntry[];
}

// --- Compliance Types ---

export interface ActualSession {
  session_id: number;
  workout_type: string;
  training_type_effective: string | null;
  duration_sec: number | null;
  distance_km: number | null;
  pace: string | null;
  planned_entry_id?: number | null;
  // Strength-specific (#149)
  total_tonnage_kg: number | null;
  exercise_count: number | null;
  set_count: number | null;
  template_name: string | null;
}

export interface ComplianceDayEntry {
  day_of_week: number;
  date: string;
  planned_types: string[];
  planned_run_type: string | null;
  is_rest_day: boolean;
  status: 'completed' | 'partial' | 'off_target' | 'missed' | 'rest_ok' | 'unplanned' | 'empty';
  actual_sessions: ActualSession[];
  // Strength planning details (#149)
  planned_template_name: string | null;
  planned_exercise_count: number | null;
}

export interface CategoryTonnage {
  category: string;
  tonnage_kg: number;
  exercise_count: number;
  set_count: number;
}

export interface WeeklyStrengthSummary {
  total_tonnage_kg: number;
  session_count: number;
  exercise_count: number;
  set_count: number;
  categories: CategoryTonnage[];
  prev_week_tonnage_kg: number | null;
  tonnage_delta_kg: number | null;
  tonnage_delta_pct: number | null;
  trend: 'up' | 'down' | 'stable' | null;
}

export interface ComplianceResponse {
  week_start: string;
  entries: ComplianceDayEntry[];
  completed_count: number;
  planned_count: number;
  strength_summary: WeeklyStrengthSummary | null;
}

// --- Sync-to-Plan Types ---

export interface SyncToPlanRequest {
  week_start: string;
  plan_id: number;
  apply_to_all_weeks: boolean;
}

export interface SyncToPlanResponse {
  phase_id: number;
  phase_name: string;
  week_key: string;
  apply_to_all_weeks: boolean;
  synced_days: number;
}

// --- Apply Recommendations Types ---

export interface ApplyRecommendationsRequest {
  week_start: string;
  recommendations: string[];
}

export interface ApplyRecommendationsResponse {
  target_week_start: string;
  entries: WeeklyPlanEntry[];
  applied_count: number;
}

// --- Undo Types ---

export interface UndoStatusResponse {
  available: boolean;
  changelog_id: number | null;
  summary: string | null;
  created_at: string | null;
  expires_at: string | null;
}

export interface UndoResponse {
  success: boolean;
  week_start: string;
  changelog_id: number;
  restored_days: number;
}

// --- Planned Session Option (for upload linking) ---

export interface PlannedSessionOption {
  id: number;
  training_type: string;
  run_type: string | null;
  template_name: string | null;
  position: number;
}

// --- API Functions ---

export async function getWeeklyPlan(weekStart?: string): Promise<WeeklyPlanResponse> {
  const params = new URLSearchParams();
  if (weekStart) params.set('week_start', weekStart);

  const url = params.toString()
    ? `/api/v1/weekly-plan?${params.toString()}`
    : '/api/v1/weekly-plan';

  const response = await apiClient.get<WeeklyPlanResponse>(url);
  return response.data;
}

export async function saveWeeklyPlan(data: WeeklyPlanSaveRequest): Promise<WeeklyPlanResponse> {
  const response = await apiClient.put<WeeklyPlanResponse>('/api/v1/weekly-plan', data);
  return response.data;
}

export async function clearWeeklyPlan(weekStart?: string): Promise<{ success: boolean }> {
  const params = new URLSearchParams();
  if (weekStart) params.set('week_start', weekStart);

  const url = params.toString()
    ? `/api/v1/weekly-plan?${params.toString()}`
    : '/api/v1/weekly-plan';

  const response = await apiClient.delete<{ success: boolean }>(url);
  return response.data;
}

export async function syncToPlan(data: SyncToPlanRequest): Promise<SyncToPlanResponse> {
  const response = await apiClient.post<SyncToPlanResponse>(
    '/api/v1/weekly-plan/sync-to-plan',
    data,
  );
  return response.data;
}

export async function getCompliance(weekStart?: string): Promise<ComplianceResponse> {
  const params = new URLSearchParams();
  if (weekStart) params.set('week_start', weekStart);

  const url = params.toString()
    ? `/api/v1/weekly-plan/compliance?${params.toString()}`
    : '/api/v1/weekly-plan/compliance';

  const response = await apiClient.get<ComplianceResponse>(url);
  return response.data;
}

export async function applyRecommendations(
  data: ApplyRecommendationsRequest,
): Promise<ApplyRecommendationsResponse> {
  const response = await apiClient.post<ApplyRecommendationsResponse>(
    '/api/v1/weekly-plan/apply-recommendations',
    data,
  );
  return response.data;
}

export async function getUndoStatus(weekStart: string): Promise<UndoStatusResponse> {
  const response = await apiClient.get<UndoStatusResponse>(
    `/api/v1/weekly-plan/undo-status?week_start=${weekStart}`,
  );
  return response.data;
}

export async function undoWeeklyPlan(weekStart: string): Promise<UndoResponse> {
  const response = await apiClient.post<UndoResponse>(
    `/api/v1/weekly-plan/undo?week_start=${weekStart}`,
  );
  return response.data;
}

export async function getPlannedSessionsForDate(date: string): Promise<PlannedSessionOption[]> {
  const response = await apiClient.get<PlannedSessionOption[]>(
    `/api/v1/weekly-plan/sessions-for-date?date=${date}`,
  );
  return response.data;
}

// --- FIT Export (#352) ---

export async function exportPlannedSessionFit(entryId: number): Promise<void> {
  const response = await apiClient.get(`/api/v1/weekly-plan/entry/${entryId}/export/fit`, {
    responseType: 'blob',
  });
  const contentDisposition = String(response.headers['content-disposition'] || '');
  const match = contentDisposition.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] || 'workout.fit';

  const url = URL.createObjectURL(response.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
