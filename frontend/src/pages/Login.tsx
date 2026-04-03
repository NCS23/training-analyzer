import { useEffect, useRef, useState } from 'react';
import {
  AuthLayout,
  Heading,
  Text,
  Button,
  InputField,
  PasswordInput,
  Separator,
  Spinner,
  Link,
} from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';

/* ------------------------------------------------------------------ */
/*  Apple SDK hook                                                      */
/* ------------------------------------------------------------------ */

function useAppleSdk(clientId: string | null, redirectUri: string | null) {
  const [ready, setReady] = useState(false);
  const initDone = useRef(false);

  useEffect(() => {
    if (!clientId || !redirectUri || initDone.current) return;

    const initSdk = () => {
      if (typeof AppleID === 'undefined') return;
      AppleID.auth.init({
        clientId,
        scope: 'name email',
        redirectURI: redirectUri,
        usePopup: true,
      });
      initDone.current = true;
      setReady(true);
    };

    if (typeof AppleID !== 'undefined') {
      initSdk();
    } else {
      const checkInterval = setInterval(() => {
        if (typeof AppleID !== 'undefined') {
          clearInterval(checkInterval);
          initSdk();
        }
      }, 100);
      return () => clearInterval(checkInterval);
    }
  }, [clientId, redirectUri]);

  return ready;
}

/* ------------------------------------------------------------------ */
/*  Email form                                                          */
/* ------------------------------------------------------------------ */

function EmailLoginForm({
  isLoading,
  onSubmit,
}: {
  isLoading: boolean;
  onSubmit: (email: string, password: string) => void;
}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <InputField
        label="E-Mail"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="name@beispiel.de"
        required
        autoComplete="email"
      />

      <PasswordInput
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Passwort"
        required
        autoComplete="current-password"
      />

      <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isLoading}>
        {isLoading ? <Spinner size="sm" /> : 'Anmelden'}
      </Button>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  Login page                                                          */
/* ------------------------------------------------------------------ */

export default function Login() {
  const {
    isLoading,
    error,
    clearError,
    appleClientId,
    appleRedirectUri,
    emailAuthEnabled,
    signInWithApple,
    signInWithEmail,
  } = useAuth();

  const sdkReady = useAppleSdk(appleClientId, appleRedirectUri);

  const handleAppleSignIn = async () => {
    clearError();
    try {
      const response = await AppleID.auth.signIn();
      const { id_token, code } = response.authorization;
      const firstName = response.user?.name?.firstName;
      await signInWithApple(id_token, code, firstName);
    } catch (err) {
      if (err instanceof Error && err.message !== 'popup_closed_by_user') {
        useAuth.setState({
          error: 'Apple-Anmeldung fehlgeschlagen. Bitte erneut versuchen.',
        });
      }
    }
  };

  const handleEmailSignIn = (email: string, password: string) => {
    clearError();
    void signInWithEmail(email, password);
  };

  return (
    <AuthLayout
      logo={
        <div className="flex items-center gap-3">
          <Heading level={3}>Training Analyzer</Heading>
        </div>
      }
      footer={
        <div className="flex items-center justify-center gap-4">
          <Link href="/register">Registrieren</Link>
        </div>
      }
    >
      <Heading level={2} className="mb-6">
        Anmelden
      </Heading>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-3 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
        >
          {error}
        </div>
      )}

      {appleClientId && (
        <Button
          variant="secondary"
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
      )}

      {emailAuthEnabled && appleClientId && (
        <>
          <Separator className="my-4" />
          <Text variant="muted" className="mb-4 text-center">
            Oder mit E-Mail
          </Text>
        </>
      )}

      {emailAuthEnabled && <EmailLoginForm isLoading={isLoading} onSubmit={handleEmailSignIn} />}
    </AuthLayout>
  );
}
