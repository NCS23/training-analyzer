import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '@/api/auth';
import { appleSignIn, getAuthStatus, getMe, logout as apiLogout, refreshTokens } from '@/api/auth';
import { apiClient } from '@/api/client';

interface AuthState {
  /** Ob Auth im Backend aktiviert ist. */
  authEnabled: boolean;
  /** Ob der User authentifiziert ist. */
  isAuthenticated: boolean;
  /** Ob der Auth-Status geladen wird. */
  isLoading: boolean;
  /** Aktueller User (oder null). */
  user: UserResponse | null;
  /** Access-Token (nur in-memory, nicht persistiert). */
  accessToken: string | null;
  /** Refresh-Token (persistiert). */
  refreshToken: string | null;
  /** Fehler-Nachricht. */
  error: string | null;
  /** Apple Client ID vom Backend (fuer SDK-Init). */
  appleClientId: string | null;
  /** Apple Redirect URI vom Backend (fuer SDK-Init). */
  appleRedirectUri: string | null;

  /** Auth-Status vom Backend laden. */
  checkStatus: () => Promise<void>;
  /** Apple Sign-In durchfuehren. */
  signInWithApple: (idToken: string, authCode: string, name?: string) => Promise<void>;
  /** Ausloggen. */
  logout: () => Promise<void>;
  /** Access-Token erneuern. */
  refresh: () => Promise<boolean>;
  /** Fehler zuruecksetzen. */
  clearError: () => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      authEnabled: false,
      isAuthenticated: false,
      isLoading: true,
      user: null,
      accessToken: null,
      refreshToken: null,
      error: null,
      appleClientId: null,
      appleRedirectUri: null,

      checkStatus: async () => {
        set({ isLoading: true, error: null });
        try {
          const status = await getAuthStatus();
          set({
            authEnabled: status.auth_enabled,
            appleClientId: status.apple_client_id ?? null,
            appleRedirectUri: status.redirect_uri ?? null,
          });

          if (!status.auth_enabled) {
            // Kein Auth → Default-User laden
            const user = await getMe();
            set({ isAuthenticated: true, user, isLoading: false });
            return;
          }

          // Auth aktiviert → pruefen ob Token vorhanden
          const { refreshToken } = get();
          if (refreshToken) {
            const success = await get().refresh();
            if (success) {
              const user = await getMe();
              set({ isAuthenticated: true, user, isLoading: false });
              return;
            }
          }

          set({ isAuthenticated: false, user: null, isLoading: false });
        } catch {
          set({ isAuthenticated: false, isLoading: false });
        }
      },

      signInWithApple: async (idToken, authCode, name) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await appleSignIn(idToken, authCode, name);
          set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });

          // Auth-Header setzen
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;

          const user = await getMe();
          set({ isAuthenticated: true, user, isLoading: false });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login fehlgeschlagen';
          set({ error: message, isLoading: false });
        }
      },

      logout: async () => {
        const { refreshToken } = get();
        if (refreshToken) {
          try {
            await apiLogout(refreshToken);
          } catch {
            // Ignorieren — Token wird lokal geloescht
          }
        }
        delete apiClient.defaults.headers.common['Authorization'];
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
        });
      },

      refresh: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;

        try {
          const tokens = await refreshTokens(refreshToken);
          set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;
          return true;
        } catch {
          // Refresh fehlgeschlagen → ausloggen
          set({
            isAuthenticated: false,
            user: null,
            accessToken: null,
            refreshToken: null,
          });
          delete apiClient.defaults.headers.common['Authorization'];
          return false;
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'training-analyzer-auth',
      partialize: (state) => ({
        refreshToken: state.refreshToken,
      }),
    },
  ),
);
