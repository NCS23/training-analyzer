import { apiClient } from './client';

export interface UserSettings {
  claude_api_key_masked: string | null;
  openai_api_key_masked: string | null;
  claude_api_key_set: boolean;
  openai_api_key_set: boolean;
}

export async function getUserSettings(): Promise<UserSettings> {
  const response = await apiClient.get<UserSettings>('/api/v1/user/settings');
  return response.data;
}

export async function updateUserSettings(params: {
  claude_api_key?: string | null;
  openai_api_key?: string | null;
}): Promise<UserSettings> {
  const response = await apiClient.patch<UserSettings>('/api/v1/user/settings', params);
  return response.data;
}
