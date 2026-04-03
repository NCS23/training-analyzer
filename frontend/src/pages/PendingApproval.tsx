import { AuthLayout, Heading, Text, Button, Spinner } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';

export default function PendingApproval() {
  const { isLoading, checkStatus, logout } = useAuth();

  return (
    <AuthLayout>
      {/* Hourglass icon */}
      <div className="mb-4 flex justify-center">
        <svg
          className="h-16 w-16 text-[var(--color-text-muted)]"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M5 22h14" />
          <path d="M5 2h14" />
          <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22" />
          <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2" />
        </svg>
      </div>

      <div className="mb-6 text-center">
        <Heading level={2} className="mb-2">
          Warte auf Freischaltung
        </Heading>
        <Text variant="muted">
          Dein Konto wurde erstellt. Ein Administrator muss es freischalten.
        </Text>
      </div>

      <div className="space-y-3">
        <Button
          variant="primary"
          size="lg"
          className="w-full"
          onClick={() => checkStatus()}
          disabled={isLoading}
        >
          {isLoading ? <Spinner size="sm" /> : 'Erneut prüfen'}
        </Button>

        <Button
          variant="ghost"
          size="lg"
          className="w-full"
          onClick={() => logout()}
          disabled={isLoading}
        >
          Abmelden
        </Button>
      </div>
    </AuthLayout>
  );
}
