import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Authorization Header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('ta_access_token');
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

  const refreshToken = localStorage.getItem('ta_refresh_token');
  if (!refreshToken) {
    isRefreshing = false;
    processQueue(new Error('No refresh token'), null);
    return Promise.reject(new Error('No refresh token'));
  }

  try {
    const resp = await apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
    const { access_token, refresh_token } = resp.data;
    localStorage.setItem('ta_access_token', access_token);
    localStorage.setItem('ta_refresh_token', refresh_token);
    originalRequest.headers.Authorization = `Bearer ${access_token}`;
    processQueue(null, access_token);
    return apiClient(originalRequest);
  } catch (refreshError) {
    processQueue(refreshError, null);
    localStorage.removeItem('ta_access_token');
    localStorage.removeItem('ta_refresh_token');
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
