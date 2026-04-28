import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const ACCESS_TOKEN_KEY = 'ta_access_token';
const REFRESH_TOKEN_KEY = 'ta_refresh_token';
// Zustand persist-Storage-Key fuer den Auth-Store (siehe useAuth.ts:persist.name).
// Wird beim Token-Cleanup mit-geloescht, damit Browser-Reload nicht stillschweigend
// einen abgelaufenen/invaliden Token rehydratet (#769).
const ZUSTAND_AUTH_KEY = 'training-analyzer-auth';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Aktuelles Access-Token aus localStorage, oder null. */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/** Tokens loeschen und zum Login navigieren — bei abgelaufenem Refresh-Token.
 *
 * Loescht ALLE Auth-Storages: flache Keys (ta_access_token/ta_refresh_token)
 * UND den zustand-persist-Store (training-analyzer-auth). Sonst wuerde der
 * persist-Store beim naechsten Reload den Token rehydrieren und den
 * onRehydrateStorage-Sync (#767) wuerde die geloeschten flachen Keys gleich
 * wieder befuellen — der User waere stillschweigend "wieder eingeloggt"
 * mit einem invaliden Token, und /login wuerde NotFound zeigen, weil
 * AuthGuard isAuthenticated=true sieht (#769).
 */
export function clearTokensAndRedirectToLogin(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(ZUSTAND_AUTH_KEY);
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

/**
 * Erzwingt einen Token-Refresh und gibt das neue Access-Token zurueck.
 * Wird sowohl vom Response-Interceptor (Axios-Calls) als auch von
 * streamChatMessage (nativer fetch-Call) genutzt.
 *
 * Wirft, wenn kein Refresh-Token da ist oder der Refresh fehlschlaegt.
 * Beide Faelle loesen den Login-Redirect aus.
 */
export async function refreshAccessTokenOrRedirect(): Promise<string> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    clearTokensAndRedirectToLogin();
    throw new Error('No refresh token');
  }
  try {
    const resp = await apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
    const { access_token, refresh_token } = resp.data as {
      access_token: string;
      refresh_token: string;
    };
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
    return access_token;
  } catch (err) {
    clearTokensAndRedirectToLogin();
    throw err;
  }
}

// Request interceptor: Authorization Header
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Token Refresh Logik
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (token) prom.resolve(token);
    else prom.reject(error);
  });
  failedQueue = [];
}

function isAuthEndpoint(url?: string): boolean {
  if (!url) return false;
  return (
    url.includes('/auth/refresh') ||
    url.includes('/auth/apple') ||
    url.includes('/auth/login') ||
    url.includes('/auth/register')
  );
}

function shouldAttemptRefresh(error: AxiosError): boolean {
  const request = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
  return error.response?.status === 401 && !request?._retry && !isAuthEndpoint(request?.url);
}

function enqueueFailedRequest(originalRequest: InternalAxiosRequestConfig) {
  return new Promise((resolve, reject) => {
    failedQueue.push({
      resolve: (token: string) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        resolve(apiClient(originalRequest));
      },
      reject,
    });
  });
}

async function attemptTokenRefresh(
  originalRequest: InternalAxiosRequestConfig & { _retry?: boolean },
) {
  originalRequest._retry = true;
  isRefreshing = true;

  try {
    const accessToken = await refreshAccessTokenOrRedirect();
    originalRequest.headers.Authorization = `Bearer ${accessToken}`;
    processQueue(null, accessToken);
    return apiClient(originalRequest);
  } catch (refreshError) {
    processQueue(refreshError, null);
    return Promise.reject(refreshError);
  } finally {
    isRefreshing = false;
  }
}

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (axios.isAxiosError(error) && shouldAttemptRefresh(error) && error.config) {
      if (isRefreshing) {
        return enqueueFailedRequest(error.config);
      }
      return attemptTokenRefresh(error.config);
    }

    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      console.error(
        `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${message}`,
      );
    }
    return Promise.reject(error);
  },
);
