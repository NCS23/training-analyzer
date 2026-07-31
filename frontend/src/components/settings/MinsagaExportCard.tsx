// MinsagaExportCard — Export für die minsaga-App-Migration (#821).
//
// Sammelt Profilwerte, Ziele und Trainingspläne (inkl. Phasen-Details)
// über die bestehenden APIs und lädt ein minsaga-export.json herunter,
// das die iOS-App im Profil einliest. Workouts sind bewusst nicht dabei.

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
import { getAthleteSettings } from '@/api/athlete';
import { listGoals } from '@/api/goals';
import { getTrainingPlan, listTrainingPlans } from '@/api/training-plans';
import { buildMinsagaExport, downloadMinsagaExportFile } from '@/utils/minsagaExport';

export function MinsagaExportCard() {
  const { toast } = useToast();
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);
    try {
      const [athlete, goalsResponse, plansResponse] = await Promise.all([
        getAthleteSettings(),
        listGoals(),
        listTrainingPlans(),
      ]);
      // Die Liste liefert nur Summaries — Phasen kommen aus dem Detail.
      const plans = await Promise.all(
        plansResponse.plans.map((summary) => getTrainingPlan(summary.id)),
      );
      const exportData = buildMinsagaExport(athlete, goalsResponse.goals, plans);
      downloadMinsagaExportFile(exportData);
      toast({
        title: `Export erstellt: ${exportData.goals.length} Ziele, ${exportData.plans.length} Pläne`,
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
            Ziele, Trainingspläne und Profilwerte als minsaga-export.json — in der minsaga-App unter
            Profil → „Aus Training Analyzer importieren" einlesen. Deine Workouts kommen dort aus
            Apple Health.
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
