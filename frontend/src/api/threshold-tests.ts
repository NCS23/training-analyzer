import { apiClient } from './client';
import type { KarvonenZone } from './athlete';

export interface ThresholdTest {
  id: number;
  test_date: string;
  lthr: number;
  max_hr_measured: number | null;
  avg_pace_sec: number | null;
  session_id: number | null;
  notes: string | null;
  created_at: string;
  friel_zones: KarvonenZone[] | null;
}

export interface ThresholdTestListResponse {
  tests: ThresholdTest[];
  total: number;
}

export interface ThresholdAnalysis {
  session_id: number;
  session_date: string;
  duration_minutes: number;
  lthr: number;
  max_hr_measured: number;
  avg_pace_sec: number | null;
  friel_zones: KarvonenZone[];
  hr_sample_count: number;
}

export interface ThresholdTestCreate {
  test_date: string;
  lthr: number;
  max_hr_measured?: number | null;
  avg_pace_sec?: number | null;
  session_id?: number | null;
  notes?: string | null;
}

export async function listThresholdTests(): Promise<ThresholdTestListResponse> {
  const response = await apiClient.get<ThresholdTestListResponse>('/api/v1/threshold-tests');
  return response.data;
}

export async function getLatestThresholdTest(): Promise<ThresholdTest> {
  const response = await apiClient.get<ThresholdTest>('/api/v1/threshold-tests/latest');
  return response.data;
}

export async function analyzeSession(sessionId: number): Promise<ThresholdAnalysis> {
  const response = await apiClient.get<ThresholdAnalysis>(
    `/api/v1/threshold-tests/analyze/${sessionId}`,
  );
  return response.data;
}

export async function createThresholdTest(data: ThresholdTestCreate): Promise<ThresholdTest> {
  const response = await apiClient.post<ThresholdTest>('/api/v1/threshold-tests', data);
  return response.data;
}

export async function deleteThresholdTest(testId: number): Promise<void> {
  await apiClient.delete(`/api/v1/threshold-tests/${testId}`);
}
