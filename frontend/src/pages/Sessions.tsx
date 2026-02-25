import { useNavigate } from 'react-router-dom';
import { Button, Card, CardBody } from '@nordlig/components';
import { Upload } from 'lucide-react';

export function SessionsPage() {
  const navigate = useNavigate();

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Sessions</h1>
        <Button variant="primary" size="sm" onClick={() => navigate('/sessions/new')}>
          <Upload className="w-4 h-4 mr-2" />
          Hochladen
        </Button>
      </div>

      <Card elevation="raised">
        <CardBody className="flex flex-col items-center py-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            Keine Sessions gefunden. Lade dein erstes Training hoch.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
