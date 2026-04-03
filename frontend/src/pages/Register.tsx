import { useState } from 'react';
import { Card, Button, Spinner, Input, Label } from '@nordlig/components';
import { useAuth } from '@/hooks/useAuth';

/* ------------------------------------------------------------------ */
/*  Register form                                                       */
/* ------------------------------------------------------------------ */

function RegisterForm({
  isLoading,
  onSubmit,
}: {
  isLoading: boolean;
  onSubmit: (email: string, password: string, name?: string) => void;
}) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (password.length < 8) {
      setLocalError('Passwort muss mindestens 8 Zeichen lang sein.');
      return;
    }
    if (password !== passwordConfirm) {
      setLocalError('Passwörter stimmen nicht überein.');
      return;
    }

    onSubmit(email, password, name || undefined);
  };

  return (
    <>
      {localError && (
        <div
          role="alert"
          className="rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-3 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
        >
          {localError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="register-name">Name (optional)</Label>
          <Input
            id="register-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Dein Name"
            autoComplete="name"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="register-email">E-Mail</Label>
          <Input
            id="register-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@beispiel.de"
            required
            autoComplete="email"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="register-password">Passwort</Label>
          <Input
            id="register-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mindestens 8 Zeichen"
            required
            minLength={8}
            autoComplete="new-password"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="register-password-confirm">Passwort bestätigen</Label>
          <Input
            id="register-password-confirm"
            type="password"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            placeholder="Passwort wiederholen"
            required
            minLength={8}
            autoComplete="new-password"
          />
        </div>

        <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isLoading}>
          {isLoading ? <Spinner size="sm" /> : 'Registrieren'}
        </Button>

        <p className="text-center text-[length:var(--font-size-sm)] text-[var(--color-text-secondary)]">
          Bereits ein Konto?{' '}
          <a href="/login" className="font-medium text-[var(--color-text-primary)] hover:underline">
            Anmelden
          </a>
        </p>
      </form>
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                                */
/* ------------------------------------------------------------------ */

export default function Register() {
  const { isLoading, error, clearError, register } = useAuth();

  const handleRegister = (email: string, password: string, name?: string) => {
    clearError();
    void register(email, password, name);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <div className="space-y-6 p-6">
          <div className="text-center">
            <h1 className="text-[length:var(--font-size-xl)] font-semibold text-[var(--color-text-primary)]">
              Registrieren
            </h1>
            <p className="mt-2 text-[length:var(--font-size-sm)] text-[var(--color-text-secondary)]">
              Erstelle ein neues Konto
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

          <RegisterForm isLoading={isLoading} onSubmit={handleRegister} />
        </div>
      </Card>
    </div>
  );
}
