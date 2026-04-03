import { apiClient } from './client';

export interface AdminUser {
  id: number;
  email: string;
  name: string | null;
  role: string;
  is_active: boolean;
  has_password: boolean;
  has_apple: boolean;
  created_at: string;
  last_login_at: string | null;
}

export const getUsers = () => apiClient.get<AdminUser[]>('/api/v1/admin/users').then((r) => r.data);

export const updateUser = (id: number, data: { role?: string; is_active?: boolean }) =>
  apiClient.patch<AdminUser>(`/api/v1/admin/users/${id}`, data).then((r) => r.data);

export const deactivateUser = (id: number) =>
  apiClient.delete(`/api/v1/admin/users/${id}`).then((r) => r.data);
