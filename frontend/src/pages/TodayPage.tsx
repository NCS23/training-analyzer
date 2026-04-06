import { Spinner, Alert, AlertDescription, Button } from '@nordlig/components';
import { Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToday } from '@/api/fitness';
import { ScoreSection } from '@/components/today/ScoreSection';
import { LastSession } from '@/components/today/LastSession';
import { WeekProgress } from '@/components/today/WeekProgress';
import { InsightCards } from '@/components/today/InsightCards';

export function TodayPage() {
  const { data, isLoading, isError, refetch } = useToday();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 pt-6 max-w-5xl mx-auto space-y-3">
        <Alert variant="error">
          <AlertDescription>Fehler beim Laden des Dashboards.</AlertDescription>
        </Alert>
        <Button variant="secondary" size="sm" onClick={() => refetch()}>
          Erneut versuchen
        </Button>
      </div>
    );
  }

  return (
    <main className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-4 pb-24">
      {/* Begrüßung */}
      <header className="pb-2">
        <h1 className="text-2xl font-bold text-[var(--color-text-base)]">{data.greeting}</h1>
      </header>

      {/* Fitness-Score */}
      <ScoreSection data={data.fitness_score} />

      {/* Wochenfortschritt */}
      <WeekProgress data={data.week_progress} />

      {/* Letzte Session */}
      {data.last_session ? (
        <LastSession session={data.last_session} />
      ) : (
        <NoSessionCard onUpload={() => navigate('/sessions/new')} />
      )}

      {/* Insights */}
      {data.insights.length > 0 && <InsightCards insights={data.insights} />}
    </main>
  );
}

function NoSessionCard({ onUpload }: { onUpload: () => void }) {
  return (
    <section aria-label="Keine Sessions vorhanden">
      <div className="rounded-[var(--radius-component-md)] border border-dashed border-[var(--color-border-default)] p-6 text-center space-y-3">
        <p className="text-sm text-[var(--color-text-muted)]">Noch kein Training erfasst.</p>
        <Button variant="primary" size="sm" onClick={onUpload}>
          <Upload className="h-4 w-4 mr-1.5" />
          Training hochladen
        </Button>
      </div>
    </section>
  );
}
