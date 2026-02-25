import { useNavigate } from 'react-router-dom';
import { Button, Card, CardBody } from '@nordlig/components';
import { Upload } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Dashboard</h1>

      <Card elevation="raised">
        <CardBody className="flex flex-col items-center py-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Noch keine Trainings vorhanden. Lade dein erstes Training hoch.
          </p>
          <Button variant="primary" onClick={() => navigate('/sessions/new')}>
            <Upload className="w-4 h-4 mr-2" />
            Training hochladen
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
