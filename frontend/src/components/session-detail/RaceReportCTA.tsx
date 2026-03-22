import { Link } from 'react-router-dom';
import { Card, CardBody, Button } from '@nordlig/components';
import { Trophy } from 'lucide-react';

interface RaceReportCTAProps {
  sessionId: number;
}

export function RaceReportCTA({ sessionId }: RaceReportCTAProps) {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-[var(--color-bg-primary-subtle)]">
            <Trophy className="w-5 h-5 text-[var(--color-text-primary)]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--color-text-base)]">Wettkampf-Bericht</p>
            <p className="text-xs text-[var(--color-text-muted)]">
              Pacing, Zielvergleich, HR-Analyse und Learnings
            </p>
          </div>
          <Link to={`/sessions/${sessionId}/race-report`}>
            <Button variant="primary" size="sm">
              Anzeigen
            </Button>
          </Link>
        </div>
      </CardBody>
    </Card>
  );
}
