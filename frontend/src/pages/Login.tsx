import { useEffect, useRef, useState } from 'react';
import { Card, Button, Spinner } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';

export default function Login() {
  const { isLoading, error, clearError, appleClientId, appleRedirectUri, signInWithApple } =
    useAuth();

  const [sdkReady, setSdkReady] = useState(false);
  const initDone = useRef(false);

  // Apple JS SDK initialisieren sobald clientId vorhanden
  useEffect(() => {
    if (!appleClientId || !appleRedirectUri || initDone.current) return;

    const initSdk = () => {
      if (typeof AppleID === 'undefined') return;
      AppleID.auth.init({
        clientId: appleClientId,
        scope: 'name email',
        redirectURI: appleRedirectUri,
        usePopup: true,
      });
      initDone.current = true;
      setSdkReady(true);
    };

    // SDK ist moeglicherweise schon geladen
    if (typeof AppleID !== 'undefined') {
      initSdk();
    } else {
      // Auf das Script warten
      const checkInterval = setInterval(() => {
        if (typeof AppleID !== 'undefined') {
          clearInterval(checkInterval);
          initSdk();
        }
      }, 100);
      return () => clearInterval(checkInterval);
    }
  }, [appleClientId, appleRedirectUri]);

  const handleAppleSignIn = async () => {
    clearError();
    try {
      const response = await AppleID.auth.signIn();
      const { id_token, code } = response.authorization;
      const firstName = response.user?.name?.firstName;
      await signInWithApple(id_token, code, firstName);
    } catch (err) {
      // User hat Popup geschlossen oder anderer Fehler
      if (err instanceof Error && err.message !== 'popup_closed_by_user') {
        useAuth.setState({
          error: 'Apple-Anmeldung fehlgeschlagen. Bitte erneut versuchen.',
        });
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <div className="space-y-6 p-6">
          <div className="text-center">
            <h1 className="text-[length:var(--font-size-xl)] font-semibold text-[var(--color-text-primary)]">
              Training Analyzer
            </h1>
            <p className="mt-2 text-[length:var(--font-size-sm)] text-[var(--color-text-secondary)]">
              Melde dich an, um fortzufahren
            </p>
          </div>

          {error && (
            <div
              role="alert"
              className="rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-3 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
            >
              {error}
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            className="w-full"
            onClick={handleAppleSignIn}
            disabled={isLoading || !sdkReady}
          >
            {isLoading ? (
              <Spinner size="sm" />
            ) : (
              <>
                <svg
                  className="mr-2 h-5 w-5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.52-3.23 0-1.44.65-2.2.46-3.06-.4C3.79 16.17 4.36 9.02 8.93 8.78c1.28.06 2.17.72 2.92.76.89-.18 1.74-.88 2.92-.82 1.53.08 2.59.72 3.24 1.84-2.92 1.75-2.23 5.64.94 6.72-.55 1.43-.82 2.07-1.9 3z" />
                  <path d="M12.16 8.67c-.14-2.14 1.58-3.99 3.63-4.17.27 2.44-2.14 4.28-3.63 4.17z" />
                </svg>
                Mit Apple anmelden
              </>
            )}
          </Button>
        </div>
      </Card>
    </div>
  );
}
