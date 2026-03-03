import { apiClient } from './client';
import type { RunDetails } from './weekly-plan';

// --- Types ---

export type PhaseType = 'base' | 'build' | 'peak' | 'taper' | 'transition';
export type PlanStatus = 'draft' | 'active' | 'completed' | 'paused';

export interface PhaseFocus {
  primary: string[];
  secondary?: string[];
}

export interface PhaseTargetMetrics {
  weekly_volume_min?: number;
  weekly_volume_max?: number;
  quality_sessions_per_week?: number;
  strength_sessions_per_week?: number;
}

export type RunType =
  | 'recovery'
  | 'easy'
  | 'long_run'
  | 'progression'
  | 'tempo'
  | 'intervals'
  | 'repetitions'
  | 'fartlek'
  | 'race';

export interface PhaseWeeklyTemplateSessionEntry {
  position: number;
  training_type: 'strength' | 'running';
  run_type: RunType | null;
  template_id: number | null;
  notes: string | null;
  run_details?: RunDetails | null;
}

export interface PhaseWeeklyTemplateDayEntry {
  day_of_week: number;
  sessions: PhaseWeeklyTemplateSessionEntry[];
  is_rest_day: boolean;
  notes: string | null;
}

export type { RunDetails } from './weekly-plan';

export interface PhaseWeeklyTemplate {
  days: PhaseWeeklyTemplateDayEntry[];
}

export interface PhaseWeeklyTemplates {
  weeks: Record<string, PhaseWeeklyTemplate>;
}

export interface TrainingPhase {
  id: number;
  training_plan_id: number;
  name: string;
  phase_type: PhaseType;
  start_week: number;
  end_week: number;
  focus: PhaseFocus | null;
  target_metrics: PhaseTargetMetrics | null;
  weekly_template: PhaseWeeklyTemplate | null;
  weekly_templates: PhaseWeeklyTemplates | null;
  notes: string | null;
  created_at: string;
}

export interface GoalSummary {
  id: number;
  title: string;
}

export interface WeeklyStructure {
  rest_days: number[];
}

export interface TrainingPlan {
  id: number;
  name: string;
  description: string | null;
  goal_id: number | null;
  start_date: string;
  end_date: string;
  target_event_date: string | null;
  weekly_structure: WeeklyStructure | null;
  status: PlanStatus;
  phases: TrainingPhase[];
  goal_summary: GoalSummary | null;
  weekly_plan_week_count: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingPlanSummary {
  id: number;
  name: string;
  status: PlanStatus;
  start_date: string;
  end_date: string;
  phase_count: number;
  weekly_plan_week_count: number;
  goal_title: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrainingPlanListResponse {
  plans: TrainingPlanSummary[];
  total: number;
}

export interface GoalCreateParams {
  title: string;
  race_date?: string;
  distance_km: number;
  target_time_seconds: number;
}

export interface TrainingPlanCreateParams {
  name: string;
  description?: string;
  goal_id?: number;
  goal?: GoalCreateParams;
  start_date: string;
  end_date: string;
  target_event_date?: string;
  weekly_structure?: WeeklyStructure;
  status?: PlanStatus;
  phases?: TrainingPhaseCreateParams[];
}

export interface TrainingPlanUpdateParams {
  name?: string;
  description?: string;
  goal_id?: number;
  start_date?: string;
  end_date?: string;
  target_event_date?: string;
  weekly_structure?: WeeklyStructure;
  status?: PlanStatus;
}

export interface TrainingPhaseCreateParams {
  name: string;
  phase_type: PhaseType;
  start_week: number;
  end_week: number;
  focus?: PhaseFocus;
  target_metrics?: PhaseTargetMetrics;
  weekly_template?: PhaseWeeklyTemplate;
  weekly_templates?: PhaseWeeklyTemplates;
  notes?: string;
}

export interface TrainingPhaseUpdateParams {
  name?: string;
  phase_type?: PhaseType;
  start_week?: number;
  end_week?: number;
  focus?: PhaseFocus;
  target_metrics?: PhaseTargetMetrics;
  weekly_template?: PhaseWeeklyTemplate;
  weekly_templates?: PhaseWeeklyTemplates;
  notes?: string;
}

// --- Plan API Functions ---

export async function listTrainingPlans(status?: PlanStatus): Promise<TrainingPlanListResponse> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);

  const url = params.toString()
    ? `/api/v1/training-plans?${params.toString()}`
    : '/api/v1/training-plans';

  const response = await apiClient.get<TrainingPlanListResponse>(url);
  return response.data;
}

export async function getTrainingPlan(planId: number): Promise<TrainingPlan> {
  const response = await apiClient.get<TrainingPlan>(`/api/v1/training-plans/${planId}`);
  return response.data;
}

export async function createTrainingPlan(params: TrainingPlanCreateParams): Promise<TrainingPlan> {
  const response = await apiClient.post<TrainingPlan>('/api/v1/training-plans', params);
  return response.data;
}

export async function updateTrainingPlan(
  planId: number,
  params: TrainingPlanUpdateParams,
): Promise<TrainingPlan> {
  const response = await apiClient.patch<TrainingPlan>(`/api/v1/training-plans/${planId}`, params);
  return response.data;
}

export async function deleteTrainingPlan(
  planId: number,
  includeWeeklyPlans = false,
): Promise<void> {
  const params = includeWeeklyPlans ? '?include_weekly_plans=true' : '';
  await apiClient.delete(`/api/v1/training-plans/${planId}${params}`);
}

export async function importTrainingPlanYaml(file: File): Promise<TrainingPlan> {
  const formData = new FormData();
  formData.append('yaml_file', file);
  const response = await apiClient.post<TrainingPlan>('/api/v1/training-plans/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

// --- YAML Validation ---

export interface YamlValidationIssue {
  code: string;
  level: 'error' | 'warning';
  message: string;
  location: string | null;
}

export interface YamlValidationResult {
  valid: boolean;
  errors: YamlValidationIssue[];
  warnings: YamlValidationIssue[];
}

export async function validateTrainingPlanYaml(file: File): Promise<YamlValidationResult> {
  const formData = new FormData();
  formData.append('yaml_file', file);
  const response = await apiClient.post<YamlValidationResult>(
    '/api/v1/training-plans/validate-yaml',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

// --- Phase API Functions ---

export async function listPhases(planId: number): Promise<TrainingPhase[]> {
  const response = await apiClient.get<TrainingPhase[]>(`/api/v1/training-plans/${planId}/phases`);
  return response.data;
}

export async function addPhase(
  planId: number,
  params: TrainingPhaseCreateParams,
): Promise<TrainingPhase> {
  const response = await apiClient.post<TrainingPhase>(
    `/api/v1/training-plans/${planId}/phases`,
    params,
  );
  return response.data;
}

export async function updatePhase(
  planId: number,
  phaseId: number,
  params: TrainingPhaseUpdateParams,
): Promise<TrainingPhase> {
  const response = await apiClient.patch<TrainingPhase>(
    `/api/v1/training-plans/${planId}/phases/${phaseId}`,
    params,
  );
  return response.data;
}

export async function deletePhase(planId: number, phaseId: number): Promise<void> {
  await apiClient.delete(`/api/v1/training-plans/${planId}/phases/${phaseId}`);
}

// --- Generate Weekly Plans ---

export interface GenerateWeeklyPlansResponse {
  weeks_generated: number;
  total_weeks: number;
}

export interface GenerationPreviewResponse {
  total_generated_weeks: number;
  edited_week_count: number;
  edited_week_starts: string[];
  unedited_week_count: number;
}

export async function getGenerationPreview(planId: number): Promise<GenerationPreviewResponse> {
  const response = await apiClient.get<GenerationPreviewResponse>(
    `/api/v1/training-plans/${planId}/generation-preview`,
  );
  return response.data;
}

export async function generateWeeklyPlans(
  planId: number,
  strategy: 'all' | 'unedited_only' = 'all',
): Promise<GenerateWeeklyPlansResponse> {
  const response = await apiClient.post<GenerateWeeklyPlansResponse>(
    `/api/v1/training-plans/${planId}/generate?strategy=${strategy}`,
    {},
  );
  return response.data;
}

// --- Change Log ---

export type ChangelogCategory = 'content' | 'structure' | 'technical' | 'meta';

export interface FieldChange {
  field: string;
  from: unknown;
  to: unknown;
  label: string;
}

export interface DayChange {
  day_of_week: number;
  day_name: string;
  field_changes: FieldChange[];
}

export interface ChangelogDetails {
  source?: string;
  category?: string;
  field_changes?: FieldChange[];
  changed_days?: DayChange[];
  phase_name?: string;
  phase_type?: string;
  phase_count?: number;
  weeks_generated?: number;
  strategy?: string;
  filename?: string;
  week_start?: string;
  apply_to_all_weeks?: boolean;
  synced_days?: number;
  /** Legacy: flat list of changed field names */
  changed_fields?: string[];
  [key: string]: unknown;
}

export interface PlanChangeLogEntry {
  id: number;
  plan_id: number;
  change_type: string;
  category: ChangelogCategory | null;
  summary: string;
  details: ChangelogDetails | null;
  reason: string | null;
  created_by: string | null;
  created_at: string;
}

export interface PlanChangeLogResponse {
  entries: PlanChangeLogEntry[];
  total: number;
}

export async function getChangelog(
  planId: number,
  limit = 50,
  offset = 0,
  category?: ChangelogCategory,
): Promise<PlanChangeLogResponse> {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  if (category) params.set('category', category);
  const response = await apiClient.get<PlanChangeLogResponse>(
    `/api/v1/training-plans/${planId}/changelog?${params.toString()}`,
  );
  return response.data;
}

export async function updateChangelogReason(
  planId: number,
  logId: number,
  reason: string,
): Promise<PlanChangeLogEntry> {
  const response = await apiClient.patch<PlanChangeLogEntry>(
    `/api/v1/training-plans/${planId}/changelog/${logId}`,
    { reason },
  );
  return response.data;
}
