import { apiClient } from './client';

export interface TrainingUploadParams {
  csvFile: File;
  trainingDate: string;
  trainingType: 'running' | 'strength';
  trainingSubtype?: string;
  notes?: string;
}

export interface TrainingUploadResponse {
  success: boolean;
  session_id?: number;
  data?: Record<string, unknown>;
  errors?: string[];
  metadata?: Record<string, unknown>;
}

export async function uploadTraining(
  params: TrainingUploadParams,
): Promise<TrainingUploadResponse> {
  const formData = new FormData();
  formData.append('csv_file', params.csvFile);
  formData.append('training_date', params.trainingDate);
  formData.append('training_type', params.trainingType);
  if (params.trainingSubtype) {
    formData.append('training_subtype', params.trainingSubtype);
  }
  if (params.notes) {
    formData.append('notes', params.notes);
  }

  const response = await apiClient.post<TrainingUploadResponse>(
    '/api/v1/sessions/upload/csv',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );

  return response.data;
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>('/health');
  return response.data;
}
