import { apiClient } from './client';

export interface TrainingUploadParams {
  csvFile: File; // Kept for backwards compat, supports CSV and FIT
  trainingDate: string;
  trainingType: 'running' | 'strength';
  trainingSubtype?: string;
  notes?: string;
  lapOverrides?: Record<number, string>;
  trainingTypeOverride?: string;
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

export async function listSessions(page = 1, pageSize = 20): Promise<SessionListResult> {
  const response = await apiClient.get<SessionListApiResponse>(
    `/api/v1/sessions?page=${page}&page_size=${pageSize}`,
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
  if (params.lapOverrides && Object.keys(params.lapOverrides).length > 0) {
    formData.append('lap_overrides_json', JSON.stringify(params.lapOverrides));
  }
  if (params.trainingTypeOverride) {
    formData.append('training_type_override', params.trainingTypeOverride);
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
  laps: LapDetail[] | null;
  hr_zones: Record<string, HRZone> | null;
  has_gps: boolean;
  athlete_resting_hr: number | null;
  athlete_max_hr: number | null;
  created_at: string;
  updated_at: string;
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
  avg_hr_bpm: number | null;
  elevation_gain_m: number | null;
  elevation_loss_m: number | null;
  is_partial: boolean;
}

export interface KmSplitsResponse {
  has_splits: boolean;
  splits: KmSplit[] | null;
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

export async function healthCheck(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>('/health');
  return response.data;
}
