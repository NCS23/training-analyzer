import { useState } from 'react';
import {
  AuthLayout,
  Heading,
  Button,
  InputField,
  PasswordInput,
  Spinner,
  Link,
  Label,
} from '@nordlig/components';
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
          className="mb-4 rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-3 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
        >
          {localError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          label="Name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Optional"
          autoComplete="name"
        />

        <InputField
          label="E-Mail"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="name@beispiel.de"
          required
          autoComplete="email"
        />

        <div>
          <Label className="mb-1">Passwort</Label>
          <PasswordInput
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min. 8 Zeichen"
            required
            autoComplete="new-password"
          />
        </div>

        <div>
          <Label className="mb-1">Passwort bestätigen</Label>
          <PasswordInput
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            placeholder="Passwort wiederholen"
            required
            autoComplete="new-password"
          />
        </div>

        <Button type="submit" variant="primary" size="lg" className="w-full" disabled={isLoading}>
          {isLoading ? <Spinner size="sm" /> : 'Registrieren'}
        </Button>
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
    <AuthLayout
      logo={
        <div className="flex items-center gap-3">
          <Heading level={3}>Training Analyzer</Heading>
        </div>
      }
      footer={
        <div className="flex items-center justify-center gap-4">
          <Link href="/login">Bereits ein Konto? Anmelden</Link>
        </div>
      }
    >
      <Heading level={2} className="mb-6">
        Konto erstellen
      </Heading>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-3 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
        >
          {error}
        </div>
      )}

      <RegisterForm isLoading={isLoading} onSubmit={handleRegister} />
    </AuthLayout>
  );
}
