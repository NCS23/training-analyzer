import { type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { Spinner } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import PendingApproval from '@/pages/PendingApproval';

interface AuthGuardProps {
  children: ReactNode;
}

/**
 * AuthGuard prueft den Auth-Status und zeigt die Login-Seite
 * wenn Auth aktiviert und der User nicht eingeloggt ist.
 *
 * checkStatus() wird automatisch nach Zustand-Rehydrierung
 * aufgerufen (onRehydrateStorage in useAuth).
 *
 * Bei auth_enabled=false wird der Content direkt gerendert.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const { authEnabled, isAuthenticated, isLoading, isPending } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Auth aktiviert aber nicht eingeloggt
  if (authEnabled && !isAuthenticated) {
    if (location.pathname === '/register') {
      return <Register />;
    }
    return <Login />;
  }

  // Pending user → Freischaltungs-Bildschirm
  if (authEnabled && isAuthenticated && isPending) {
    return <PendingApproval />;
  }

  // Auth nicht aktiviert oder User eingeloggt → Content anzeigen
  return <>{children}</>;
}
