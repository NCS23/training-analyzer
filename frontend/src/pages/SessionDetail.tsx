import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, CardBody } from '@nordlig/components';
import { ArrowLeft } from 'lucide-react';

export function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/sessions')}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Session #{id}</h1>
      </div>

      <Card elevation="raised">
        <CardBody className="flex flex-col items-center py-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            Session-Detail wird mit E01-S05 implementiert.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
