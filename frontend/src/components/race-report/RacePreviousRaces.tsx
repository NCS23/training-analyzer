import { Link } from 'react-router-dom';
import { Card, CardHeader, CardBody } from '@nordlig/components';
import { History } from 'lucide-react';
import type { PreviousRace } from '@/api/training';

interface RacePreviousRacesProps {
  races: PreviousRace[];
}

export function RacePreviousRaces({ races }: RacePreviousRacesProps) {
  if (races.length === 0) return null;

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-[var(--color-text-muted)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Vorherige Rennen</h2>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-2">
          {races.map((race) => {
            const faster = race.delta_seconds < 0;
            const absDelta = Math.abs(race.delta_seconds);
            const deltaMins = Math.floor(absDelta / 60);
            const deltaSecs = absDelta % 60;
            const deltaStr = `${faster ? '-' : '+'}${deltaMins}:${String(deltaSecs).padStart(2, '0')}`;

            return (
              <Link
                key={race.session_id}
                to={`/sessions/${race.session_id}`}
                className="flex items-center justify-between p-2 rounded-[var(--radius-sm)] hover:bg-[var(--color-bg-muted)] transition-colors"
              >
                <div>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {race.date} — {race.distance_km} km
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {race.duration_formatted} ({race.pace_formatted}/km)
                  </p>
                </div>
                <span
                  className={`text-sm font-semibold ${
                    faster ? 'text-[var(--color-text-error)]' : 'text-[var(--color-text-success)]'
                  }`}
                >
                  {deltaStr}
                </span>
              </Link>
            );
          })}
        </div>
      </CardBody>
    </Card>
  );
}
