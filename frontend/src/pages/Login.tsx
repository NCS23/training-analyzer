import { Card, Button, Spinner } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';

export default function Login() {
  const { isLoading, error, clearError } = useAuth();

  const handleAppleSignIn = async () => {
    clearError();
    // In der nativen iOS App wird das Apple Sign-In SDK aufgerufen
    // und das ID-Token + Authorization Code hier uebergeben.
    // Fuer die Web-Version: Apple JS SDK Integration.
    // Placeholder fuer die tatsaechliche Apple Sign-In Integration:
    const event = new CustomEvent('apple-sign-in-request');
    window.dispatchEvent(event);
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
            disabled={isLoading}
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
