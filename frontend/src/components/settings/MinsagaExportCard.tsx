// MinsagaExportCard — Export für die minsaga-App-Migration (#821, #823).
//
// Der Export kommt komplett vom Backend (Format-Version 2): Profil +
// Schwellentests, Ziele, Pläne mit Changelog (Entscheidungen samt
// Begründung) und alle Wochenplan-Wochen mit ihren Anpassungen.
// Workouts sind bewusst nicht dabei — die kommen aus Apple Health.

import { useState } from 'react';
import {
  Card,
  CardBody,
  Button,
  Alert,
  AlertDescription,
  Spinner,
  useToast,
} from '@nordlig/components';
import { downloadMinsagaExport } from '@/utils/minsagaExport';

export function MinsagaExportCard() {
  const { toast } = useToast();
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    try {
      const summary = await downloadMinsagaExport();
      toast({
        title: `Export erstellt: ${summary.goals} Ziele, ${summary.plans} Pläne, ${summary.weeks} Wochen`,
        variant: 'success',
      });
    } catch {
      setError('Export fehlgeschlagen — bitte erneut versuchen.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <Card elevation="raised" padding="spacious">
      <CardBody className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold">Export für minsaga</h3>
          <p className="text-xs text-[var(--color-text-muted)]">
            Kompletter Stand als minsaga-export.json: Ziele, Pläne samt Änderungshistorie, alle
            Wochenplan-Anpassungen, Schwellentests und Profilwerte — in der minsaga-App unter Profil
            → „Aus Training Analyzer importieren" einlesen. Deine Workouts kommen dort aus Apple
            Health.
          </p>
          {error && (
            <Alert variant="error" closeable onClose={() => setError(null)} className="mt-3">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>
        <Button
          variant="secondary"
          onClick={handleExport}
          disabled={exporting}
          className="shrink-0"
        >
          {exporting ? <Spinner size="sm" aria-hidden="true" /> : 'Herunterladen'}
        </Button>
      </CardBody>
    </Card>
  );
}
