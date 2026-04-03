import { apiClient } from './client';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: number;
  email: string;
  name: string | null;
  avatar_url: string | null;
  created_at: string;
}

export interface AuthStatusResponse {
  auth_enabled: boolean;
  authenticated: boolean;
  user: UserResponse | null;
  apple_client_id: string | null;
  redirect_uri: string | null;
}

/** Apple Sign-In: ID-Token gegen Access/Refresh-Token tauschen. */
export async function appleSignIn(
  idToken: string,
  authorizationCode: string,
  name?: string,
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/apple', {
    id_token: idToken,
    authorization_code: authorizationCode,
    name,
  });
  return data;
}

/** Auth-Status pruefen (auth_enabled, authenticated). */
export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const { data } = await apiClient.get<AuthStatusResponse>('/api/v1/auth/status');
  return data;
}

/** Access-Token erneuern. */
export async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  });
  return data;
}

/** Ausloggen (Refresh-Token revoken). */
export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post('/api/v1/auth/logout', {
    refresh_token: refreshToken,
  });
}

/** Eigene User-Daten abrufen. */
export async function getMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/api/v1/auth/me');
  return data;
}
