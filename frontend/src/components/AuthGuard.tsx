import { useEffect, type ReactNode } from 'react';
import { Spinner } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';
import Login from '@/pages/Login';

interface AuthGuardProps {
  children: ReactNode;
}

/**
 * AuthGuard prueft den Auth-Status und zeigt die Login-Seite
 * wenn Auth aktiviert und der User nicht eingeloggt ist.
 *
 * Bei auth_enabled=false wird der Content direkt gerendert.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const { authEnabled, isAuthenticated, isLoading, checkStatus } = useAuth();

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Auth nicht aktiviert oder User eingeloggt → Content anzeigen
  if (!authEnabled || isAuthenticated) {
    return <>{children}</>;
  }

  // Auth aktiviert aber nicht eingeloggt → Login anzeigen
  return <Login />;
}
