import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '@/api/auth';
import {
  appleSignIn,
  getAuthStatus,
  getMe,
  loginWithEmail,
  logout as apiLogout,
  refreshTokens,
  registerWithEmail,
} from '@/api/auth';
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
  /** Ob E-Mail-Auth im Backend aktiviert ist. */
  emailAuthEnabled: boolean;

  /** Auth-Status vom Backend laden. */
  checkStatus: () => Promise<void>;
  /** Apple Sign-In durchfuehren. */
  signInWithApple: (idToken: string, authCode: string, name?: string) => Promise<void>;
  /** Mit E-Mail und Passwort einloggen. */
  signInWithEmail: (email: string, password: string) => Promise<void>;
  /** Registrierung mit E-Mail und Passwort. */
  register: (email: string, password: string, name?: string) => Promise<void>;
  /** Ausloggen. */
  logout: () => Promise<void>;
  /** Access-Token erneuern. */
  refresh: () => Promise<boolean>;
  /** Fehler zuruecksetzen. */
  clearError: () => void;
  /** Ob der User die Rolle 'pending' hat. */
  isPending: boolean;
  /** Ob der User die Rolle 'admin' hat. */
  isAdmin: boolean;
}

/** Setzt Tokens im Store und im API-Client. */
function applyTokens(
  set: (state: Partial<AuthState>) => void,
  tokens: { access_token: string; refresh_token: string },
) {
  set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;
}

/** Laedt den User und setzt den authentifizierten Zustand. */
async function loadUserAndSetState(set: (state: Partial<AuthState>) => void) {
  const user = await getMe();
  set({
    isAuthenticated: true,
    user,
    isPending: user.role === 'pending',
    isAdmin: user.role === 'admin',
    isLoading: false,
  });
}

/** Setzt den abgemeldeten Zustand. */
function clearAuthState(set: (state: Partial<AuthState>) => void) {
  set({
    isAuthenticated: false,
    user: null,
    accessToken: null,
    refreshToken: null,
    isPending: false,
    isAdmin: false,
  });
  delete apiClient.defaults.headers.common['Authorization'];
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
      emailAuthEnabled: false,
      isPending: false,
      isAdmin: false,

      checkStatus: async () => {
        set({ isLoading: true, error: null });
        try {
          const status = await getAuthStatus();
          set({
            authEnabled: status.auth_enabled,
            appleClientId: status.apple_client_id ?? null,
            appleRedirectUri: status.redirect_uri ?? null,
            emailAuthEnabled: status.email_auth_enabled ?? false,
          });

          if (!status.auth_enabled) {
            await loadUserAndSetState(set);
            return;
          }

          // Auth aktiviert → pruefen ob Token vorhanden
          const { refreshToken } = get();
          if (refreshToken) {
            const success = await get().refresh();
            if (success) {
              await loadUserAndSetState(set);
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
          applyTokens(set, tokens);
          await loadUserAndSetState(set);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login fehlgeschlagen';
          set({ error: message, isLoading: false });
        }
      },

      signInWithEmail: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          applyTokens(set, await loginWithEmail(email, password));
          await loadUserAndSetState(set);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Anmeldung fehlgeschlagen';
          set({ error: message, isLoading: false });
        }
      },

      register: async (email, password, name) => {
        set({ isLoading: true, error: null });
        try {
          applyTokens(set, await registerWithEmail(email, password, name));
          await loadUserAndSetState(set);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Registrierung fehlgeschlagen';
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
        clearAuthState(set);
      },

      refresh: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;

        try {
          const tokens = await refreshTokens(refreshToken);
          applyTokens(set, tokens);
          return true;
        } catch {
          clearAuthState(set);
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
