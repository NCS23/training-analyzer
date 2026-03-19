import { apiClient } from './client';
import type { Segment } from './segment';

export interface TrainingUploadParams {
  csvFile: File; // Kept for backwards compat, supports CSV and FIT
  trainingDate: string;
  trainingType: 'running' | 'strength';
  trainingSubtype?: string;
  notes?: string;
  rpe?: number;
  lapOverrides?: Record<number, string>;
  trainingTypeOverride?: string;
  plannedEntryId?: number;
}

function isFitFile(file: File): boolean {
  return file.name.toLowerCase().endsWith('.fit');
}

export interface TrainingUploadResponse {
  success: boolean;
  session_id?: number;
  data?: Record<string, unknown>;
  errors?: string[];
  metadata?: Record<string, unknown>;
}

export interface ParsedLap {
  lap_number: number;
  duration_seconds: number;
  duration_formatted: string;
  distance_km: number | null;
  pace_min_per_km: number | null;
  pace_formatted: string | null;
  avg_hr_bpm: number | null;
  suggested_type: string | null;
  confidence: string | null;
}

export interface TrainingParseResponse {
  success: boolean;
  data?: {
    laps: ParsedLap[] | null;
    summary: {
      total_duration_seconds: number;
      total_duration_formatted?: string;
      total_distance_km?: number;
      avg_hr_bpm?: number;
      avg_pace_formatted?: string;
    };
  };
  errors?: string[];
  metadata?: {
    training_type_auto?: string | null;
    training_type_confidence?: number | null;
  };
}

export interface SessionSummary {
  id: number;
  date: string;
  workout_type: string;
  subtype: string | null;
  training_type: TrainingTypeInfo | null;
  duration_sec: number | null;
  distance_km: number | null;
  pace: string | null;
  hr_avg: number | null;
  exercises_count: number | null;
  total_tonnage_kg: number | null;
}

interface SessionListApiResponse {
  sessions: SessionSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SessionListResult {
  sessions: SessionSummary[];
  total: number;
  page: number;
  pageSize: number;
}

export interface SessionFilters {
  workoutType?: string;
  trainingType?: string;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export async function listSessions(
  page = 1,
  pageSize = 20,
  filters?: SessionFilters,
): Promise<SessionListResult> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters?.workoutType) params.set('workout_type', filters.workoutType);
  if (filters?.trainingType) params.set('training_type', filters.trainingType);
  if (filters?.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters?.dateTo) params.set('date_to', filters.dateTo);
  if (filters?.search) params.set('search', filters.search);

  const response = await apiClient.get<SessionListApiResponse>(
    `/api/v1/sessions?${params.toString()}`,
  );
  return {
    sessions: response.data.sessions,
    total: response.data.total,
    page: response.data.page,
    pageSize: response.data.page_size,
  };
}

export async function parseTraining(
  params: Omit<TrainingUploadParams, 'lapOverrides' | 'trainingTypeOverride'>,
): Promise<TrainingParseResponse> {
  const fit = isFitFile(params.csvFile);
  const formData = new FormData();
  formData.append(fit ? 'fit_file' : 'csv_file', params.csvFile);
  formData.append('training_date', params.trainingDate);
  formData.append('training_type', params.trainingType);
  if (params.trainingSubtype) {
    formData.append('training_subtype', params.trainingSubtype);
  }
  if (params.notes) {
    formData.append('notes', params.notes);
  }

  const response = await apiClient.post<TrainingParseResponse>(
    fit ? '/api/v1/sessions/parse/fit' : '/api/v1/sessions/parse',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );

  return response.data;
}

export async function uploadTraining(
  params: TrainingUploadParams,
): Promise<TrainingUploadResponse> {
  const fit = isFitFile(params.csvFile);
  const formData = new FormData();
  formData.append(fit ? 'fit_file' : 'csv_file', params.csvFile);
  formData.append('training_date', params.trainingDate);
  formData.append('training_type', params.trainingType);
  if (params.trainingSubtype) {
    formData.append('training_subtype', params.trainingSubtype);
  }
  if (params.notes) {
    formData.append('notes', params.notes);
  }
  if (params.rpe != null) {
    formData.append('rpe', String(params.rpe));
  }
  if (params.lapOverrides && Object.keys(params.lapOverrides).length > 0) {
    formData.append('lap_overrides_json', JSON.stringify(params.lapOverrides));
  }
  if (params.trainingTypeOverride) {
    formData.append('training_type_override', params.trainingTypeOverride);
  }
  if (params.plannedEntryId != null) {
    formData.append('planned_entry_id', String(params.plannedEntryId));
  }

  const response = await apiClient.post<TrainingUploadResponse>(
    fit ? '/api/v1/sessions/upload/fit' : '/api/v1/sessions/upload/csv',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );

  return response.data;
}

export interface LapOverrideParams {
  sessionId: number;
  overrides: { lap_number: number; user_override: string }[];
}

export interface LapOverrideResponse {
  success: boolean;
  laps: Record<string, unknown>[];
  summary_working?: Record<string, unknown>;
  hr_zones_working?: Record<string, unknown>;
}

export async function updateLapOverrides(params: LapOverrideParams): Promise<LapOverrideResponse> {
  const response = await apiClient.patch<LapOverrideResponse>(
    `/api/v1/sessions/${params.sessionId}/laps`,
    { overrides: params.overrides },
  );

  return response.data;
}

export interface TrainingTypeInfo {
  auto: string | null;
  confidence: number | null;
  override: string | null;
  effective: string | null;
}

export interface LapDetail {
  lap_number: number;
  duration_seconds: number;
  duration_formatted: string;
  distance_km: number | null;
  pace_min_per_km: number | null;
  pace_formatted: string | null;
  avg_hr_bpm: number | null;
  max_hr_bpm: number | null;
  min_hr_bpm: number | null;
  avg_cadence_spm: number | null;
  suggested_type: string | null;
  confidence: string | null;
  user_override: string | null;
  start_seconds: number | null;
  end_seconds: number | null;
}

export interface HRZone {
  seconds: number;
  percentage: number;
  label: string;
  zone?: number;
  name?: string;
  color?: string;
}

export interface SessionDetail {
  id: number;
  date: string;
  workout_type: string;
  subtype: string | null;
  training_type: TrainingTypeInfo | null;
  duration_sec: number | null;
  distance_km: number | null;
  pace: string | null;
  hr_avg: number | null;
  hr_max: number | null;
  hr_min: number | null;
  cadence_avg: number | null;
  notes: string | null;
  rpe: number | null;
  laps: LapDetail[] | null;
  segments?: Segment[] | null;
  hr_zones: Record<string, HRZone> | null;
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
  }> | null;
  has_gps: boolean;
  planned_entry_id: number | null;
  athlete_resting_hr: number | null;
  athlete_max_hr: number | null;
  ai_analysis: SessionAnalysis | null;
  created_at: string;
  updated_at: string;
}

export interface SessionAnalysis {
  session_id: number;
  provider: string;
  summary: string;
  intensity_rating: string;
  intensity_text: string;
  hr_zone_assessment: string;
  plan_comparison: string | null;
  fatigue_indicators: string | null;
  recommendations: string[];
  cached: boolean;
}

export async function updateTrainingType(
  sessionId: number,
  trainingType: string,
): Promise<SessionDetail> {
  const response = await apiClient.patch<SessionDetail>(
    `/api/v1/sessions/${sessionId}/training-type`,
    { training_type: trainingType },
  );
  return response.data;
}

export async function getSession(sessionId: number): Promise<SessionDetail> {
  const response = await apiClient.get<SessionDetail>(`/api/v1/sessions/${sessionId}`);
  return response.data;
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/api/v1/sessions/${sessionId}`);
}

export async function updateSessionNotes(
  sessionId: number,
  notes: string | null,
): Promise<SessionDetail> {
  const response = await apiClient.patch<SessionDetail>(`/api/v1/sessions/${sessionId}/notes`, {
    notes,
  });
  return response.data;
}

export async function updateSessionDate(sessionId: number, date: string): Promise<SessionDetail> {
  const response = await apiClient.patch<SessionDetail>(`/api/v1/sessions/${sessionId}/date`, {
    date,
  });
  return response.data;
}

export async function updateSessionRpe(
  sessionId: number,
  rpe: number | null,
): Promise<SessionDetail> {
  const response = await apiClient.patch<SessionDetail>(`/api/v1/sessions/${sessionId}/rpe`, {
    rpe,
  });
  return response.data;
}

export async function updatePlannedEntry(
  sessionId: number,
  plannedEntryId: number | null,
): Promise<SessionDetail> {
  const response = await apiClient.patch<SessionDetail>(
    `/api/v1/sessions/${sessionId}/planned-entry`,
    { planned_entry_id: plannedEntryId },
  );
  return response.data;
}

export interface GPSPoint {
  lat: number;
  lng: number;
  alt?: number;
  hr?: number;
  speed?: number; // m/s
  seconds: number;
}

export interface GPSTrack {
  points: GPSPoint[];
  start_location: { lat: number; lng: number };
  end_location: { lat: number; lng: number };
  total_points: number;
  total_ascent_m: number | null;
  total_descent_m: number | null;
}

export interface SessionTrackResponse {
  has_gps: boolean;
  track: GPSTrack | null;
}

export async function getSessionTrack(sessionId: number): Promise<SessionTrackResponse> {
  const response = await apiClient.get<SessionTrackResponse>(`/api/v1/sessions/${sessionId}/track`);
  return response.data;
}

export interface KmSplit {
  km_number: number;
  distance_km: number;
  duration_seconds: number;
  duration_formatted: string;
  pace_min_per_km: number | null;
  pace_formatted: string | null;
  pace_corrected_min_per_km: number | null;
  pace_corrected_formatted: string | null;
  avg_hr_bpm: number | null;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  is_partial: boolean;
  boundary_lat: number | null;
  boundary_lng: number | null;
}

export interface KmSplitsResponse {
  has_splits: boolean;
  splits: KmSplit[] | null;
  session_gap_min_per_km: number | null;
  session_gap_formatted: string | null;
  elevation_factors: {
    gain_sec_per_100m: number;
    loss_sec_per_100m: number;
  } | null;
}

export async function getKmSplits(sessionId: number): Promise<KmSplitsResponse> {
  const response = await apiClient.get<KmSplitsResponse>(`/api/v1/sessions/${sessionId}/km-splits`);
  return response.data;
}

export interface WorkingZonesResponse {
  hr_zones_working: Record<string, HRZone> | null;
}

export async function getWorkingZones(sessionId: number): Promise<WorkingZonesResponse> {
  const response = await apiClient.get<WorkingZonesResponse>(
    `/api/v1/sessions/${sessionId}/working-zones`,
  );
  return response.data;
}

export interface RecalculateZonesResponse {
  success: boolean;
  hr_zones: Record<string, HRZone>;
  athlete_resting_hr: number | null;
  athlete_max_hr: number | null;
}

export async function recalculateSessionZones(
  sessionId: number,
  params?: { resting_hr: number; max_hr: number },
): Promise<RecalculateZonesResponse> {
  const response = await apiClient.post<RecalculateZonesResponse>(
    `/api/v1/sessions/${sessionId}/recalculate-zones`,
    params ?? {},
  );
  return response.data;
}

// --- KI Session-Analyse (#32) ---

export async function analyzeSession(
  sessionId: number,
  forceRefresh = false,
): Promise<SessionAnalysis> {
  const response = await apiClient.post<SessionAnalysis>(`/api/v1/sessions/${sessionId}/analyze`, {
    force_refresh: forceRefresh,
  });
  return response.data;
}

// --- KI-Empfehlungen (E06-S02, #33) ---

export type RecommendationType =
  | 'adjust_pace'
  | 'adjust_volume'
  | 'add_rest'
  | 'skip_session'
  | 'increase_volume'
  | 'reduce_intensity'
  | 'change_session_type'
  | 'extend_warmup_cooldown'
  | 'general';

export type RecommendationPriority = 'high' | 'medium' | 'low';
export type RecommendationStatusValue = 'pending' | 'applied' | 'dismissed';

export interface AIRecommendation {
  id: number;
  session_id: number;
  type: RecommendationType;
  title: string;
  target_session_id: number | null;
  current_value: string | null;
  suggested_value: string | null;
  reasoning: string;
  priority: RecommendationPriority;
  status: RecommendationStatusValue;
  created_at: string;
}

export interface RecommendationsList {
  recommendations: AIRecommendation[];
  session_id: number;
  provider: string;
  cached: boolean;
}

export async function generateRecommendations(
  sessionId: number,
  forceRefresh = false,
): Promise<RecommendationsList> {
  const response = await apiClient.post<RecommendationsList>(
    `/api/v1/sessions/${sessionId}/recommendations`,
    { force_refresh: forceRefresh },
  );
  return response.data;
}

export async function getRecommendations(sessionId: number): Promise<RecommendationsList> {
  const response = await apiClient.get<RecommendationsList>(
    `/api/v1/sessions/${sessionId}/recommendations`,
  );
  return response.data;
}

export async function updateRecommendationStatus(
  recommendationId: number,
  status: RecommendationStatusValue,
): Promise<AIRecommendation> {
  const response = await apiClient.patch<AIRecommendation>(
    `/api/v1/sessions/recommendations/${recommendationId}/status`,
    { status },
  );
  return response.data;
}

// --- Soll/Ist-Vergleich (#138) ---

export interface SegmentDelta {
  pace_delta_seconds: number | null;
  pace_delta_formatted: string | null;
  hr_avg_delta: number | null;
  duration_delta_seconds: number | null;
  distance_delta_km: number | null;
}

export interface MatchedSegment {
  position: number;
  segment_type: string;
  match_quality: 'matched' | 'unmatched_planned' | 'unmatched_actual';
  planned: import('./segment').Segment | null;
  actual: import('./segment').Segment | null;
  delta: SegmentDelta | null;
}

export interface ComparisonResponse {
  planned_entry_id: number;
  planned_run_type: string | null;
  segments: MatchedSegment[];
  has_mismatch: boolean;
  planned_count: number;
  actual_count: number;
}

export async function getSessionComparison(sessionId: number): Promise<ComparisonResponse> {
  const response = await apiClient.get<ComparisonResponse>(
    `/api/v1/sessions/${sessionId}/comparison`,
  );
  return response.data;
}

// --- KI Debug Log (#261) ---

export interface AILogEntry {
  id: number;
  workout_id: number | null;
  use_case: string;
  context_label: string | null;
  created_at: string;
  provider: string;
  parsed_ok: boolean;
  duration_ms: number | null;
  session_date: string | null;
  session_type: string | null;
}

export interface AILogDetail extends AILogEntry {
  system_prompt: string;
  user_prompt: string;
  raw_response: string;
}

export interface AILogListResponse {
  items: AILogEntry[];
  total: number;
}

export async function fetchAILog(limit = 20, offset = 0): Promise<AILogListResponse> {
  const response = await apiClient.get<AILogListResponse>('/api/v1/ai/log', {
    params: { limit, offset },
  });
  return response.data;
}

export async function fetchAILogDetail(logId: number): Promise<AILogDetail> {
  const response = await apiClient.get<AILogDetail>(`/api/v1/ai/log/${logId}`);
  return response.data;
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>('/health');
  return response.data;
}

// --- Wöchentliches KI-Review (E06-S06, #323) ---

export type OverallRating = 'excellent' | 'good' | 'moderate' | 'poor';
export type FatigueLevel = 'low' | 'moderate' | 'high' | 'critical';

export interface VolumeComparison {
  planned_km: number | null;
  actual_km: number;
  planned_sessions: number | null;
  actual_sessions: number;
  planned_hours: number | null;
  actual_hours: number;
}

export interface WeeklyReview {
  id: number;
  week_start: string;
  summary: string;
  volume_comparison: VolumeComparison;
  highlights: string[];
  improvements: string[];
  next_week_recommendations: string[];
  overall_rating: OverallRating;
  fatigue_assessment: FatigueLevel;
  session_count: number;
  provider: string;
  cached: boolean;
  created_at: string;
}

export async function generateWeeklyReview(
  weekStart: string,
  forceRefresh = false,
): Promise<WeeklyReview> {
  const response = await apiClient.post<WeeklyReview>('/api/v1/weekly-review/generate', {
    week_start: weekStart,
    force_refresh: forceRefresh,
  });
  return response.data;
}

export async function getWeeklyReview(weekStart: string): Promise<WeeklyReview> {
  const response = await apiClient.get<WeeklyReview>(`/api/v1/weekly-review/${weekStart}`);
  return response.data;
}

// --- Reparse (#349) ---

export interface ReparseResponse {
  success: boolean;
  session_id: number;
  message: string;
  changes: {
    hr_avg: number | null;
    hr_max: number | null;
    hr_min: number | null;
    laps_count: number;
    has_hr_zones: boolean;
    has_gps: boolean;
    lap_overrides_restored: number;
  };
}

export async function reparseSession(sessionId: number): Promise<ReparseResponse> {
  const response = await apiClient.post<ReparseResponse>(`/api/v1/sessions/${sessionId}/reparse`);
  return response.data;
}
