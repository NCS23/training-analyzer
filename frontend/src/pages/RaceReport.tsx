import { useParams, Link } from 'react-router-dom';
import { Spinner, Alert, AlertDescription, Breadcrumbs, BreadcrumbItem } from '@nordlig/components';
import { useQuery } from '@tanstack/react-query';
import { getKmSplits, getSession } from '@/api/training';
import { useRaceReport } from '@/hooks/useRaceReport';
import { RaceReportContent } from '@/components/race-report/RaceReportContent';

export function RaceReportPage() {
  const { id } = useParams<{ id: string }>();
  const sessionId = Number(id);

  const { report, isLoading, error, analysis, isAnalyzing, triggerAnalysis } =
    useRaceReport(sessionId);

  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => getSession(sessionId),
  });

  const { data: splitsData } = useQuery({
    queryKey: ['km-splits', sessionId],
    queryFn: () => getKmSplits(sessionId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto">
        <Alert variant="error">
          <AlertDescription>Fehler beim Laden des Wettkampf-Berichts.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const sessionLabel = session?.workout_type === 'running' ? 'Lauf' : 'Session';

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator="/">
          <BreadcrumbItem>
            <Link to="/sessions">Sessions</Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to={`/sessions/${sessionId}`}>
              {sessionLabel} {session?.date ?? ''}
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>Wettkampf-Bericht</BreadcrumbItem>
        </Breadcrumbs>
        <h1 className="text-xl sm:text-2xl font-semibold text-[var(--color-text-base)]">
          Wettkampf-Bericht
        </h1>
      </div>

      {report && (
        <RaceReportContent
          report={report}
          splits={splitsData?.splits ?? []}
          analysis={analysis}
          isAnalyzing={isAnalyzing}
          onTriggerAnalysis={() => triggerAnalysis()}
        />
      )}
    </div>
  );
}
