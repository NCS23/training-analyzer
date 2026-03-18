import { apiClient } from './client';
import type { RunDetails } from './weekly-plan';

// --- Types ---

export type ExerciseType = 'kraft' | 'mobilitaet' | 'dehnung';
export type ExerciseCategory = 'push' | 'pull' | 'legs' | 'core' | 'cardio' | 'drills';

export interface TemplateExercise {
  name: string;
  category: ExerciseCategory;
  sets: number;
  reps: number;
  weight_kg: number | null;
  exercise_type: ExerciseType;
  notes: string | null;
}

export interface SessionTemplate {
  id: number;
  name: string;
  description: string | null;
  session_type: string;
  exercises: TemplateExercise[];
  run_details: RunDetails | null;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface SessionTemplateSummary {
  id: number;
  name: string;
  session_type: string;
  exercise_count: number;
  total_sets: number;
  run_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface SessionTemplateListResponse {
  templates: SessionTemplateSummary[];
  total: number;
}

export interface SessionTemplateCreateParams {
  name: string;
  description?: string;
  session_type: string;
  exercises?: TemplateExercise[];
  run_details?: RunDetails;
}

export interface SessionTemplateUpdateParams {
  name?: string;
  description?: string;
  exercises?: TemplateExercise[];
  run_details?: RunDetails;
}

// --- API Functions ---

export async function listSessionTemplates(
  sessionType?: string,
): Promise<SessionTemplateListResponse> {
  const params = new URLSearchParams();
  if (sessionType) params.set('session_type', sessionType);

  const url = params.toString()
    ? `/api/v1/session-templates?${params.toString()}`
    : '/api/v1/session-templates';

  const response = await apiClient.get<SessionTemplateListResponse>(url);
  return response.data;
}

export async function getSessionTemplate(templateId: number): Promise<SessionTemplate> {
  const response = await apiClient.get<SessionTemplate>(`/api/v1/session-templates/${templateId}`);
  return response.data;
}

export async function createSessionTemplate(
  params: SessionTemplateCreateParams,
): Promise<SessionTemplate> {
  const response = await apiClient.post<SessionTemplate>('/api/v1/session-templates', params);
  return response.data;
}

export async function updateSessionTemplate(
  templateId: number,
  params: SessionTemplateUpdateParams,
): Promise<SessionTemplate> {
  const response = await apiClient.patch<SessionTemplate>(
    `/api/v1/session-templates/${templateId}`,
    params,
  );
  return response.data;
}

export async function deleteSessionTemplate(templateId: number): Promise<void> {
  await apiClient.delete(`/api/v1/session-templates/${templateId}`);
}

export async function duplicateSessionTemplate(templateId: number): Promise<SessionTemplate> {
  const response = await apiClient.post<SessionTemplate>(
    `/api/v1/session-templates/${templateId}/duplicate`,
  );
  return response.data;
}

export async function downloadTemplateFit(templateId: number, templateName: string): Promise<void> {
  const response = await apiClient.get<Blob>(`/api/v1/session-templates/${templateId}/export/fit`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(response.data);
  const a = document.createElement('a');
  a.href = url;
  const safeName = templateName
    .replace(/[^a-z0-9]+/gi, '-')
    .toLowerCase()
    .slice(0, 50);
  const today = new Date().toISOString().split('T')[0];
  a.download = `workout-${safeName}-${today}.fit`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export async function createTemplateFromSession(sessionId: number): Promise<SessionTemplate> {
  const response = await apiClient.post<SessionTemplate>(
    `/api/v1/session-templates/from-session/${sessionId}`,
  );
  return response.data;
}
