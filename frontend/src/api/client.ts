import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error logging
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      console.error(
        `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${message}`,
      );
    }
    return Promise.reject(error);
  },
);
