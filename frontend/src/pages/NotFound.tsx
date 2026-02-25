import { useNavigate } from 'react-router-dom';
import { Button } from '@nordlig/components';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center">
      <h1 className="text-6xl font-bold text-[var(--color-text-muted)] mb-2">404</h1>
      <p className="text-sm text-[var(--color-text-muted)] mb-6">Seite nicht gefunden.</p>
      <Button variant="primary" onClick={() => navigate('/dashboard')}>
        Zum Dashboard
      </Button>
    </div>
  );
}
