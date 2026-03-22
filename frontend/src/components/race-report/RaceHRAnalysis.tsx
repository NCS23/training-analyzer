import { Card, CardHeader, CardBody, Badge } from '@nordlig/components';
import { Heart } from 'lucide-react';
import type { HRManagement } from '@/api/training';

interface RaceHRAnalysisProps {
  hr: HRManagement;
}

export function RaceHRAnalysis({ hr }: RaceHRAnalysisProps) {
  const zones = Object.entries(hr.zone_distribution)
    .filter(([, pct]) => pct > 0)
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Heart className="w-4 h-4 text-[var(--color-text-muted)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Herzfrequenz-Management
          </h2>
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex gap-4 mb-4">
          <div className="text-center">
            <p className="text-xs text-[var(--color-text-muted)]">Ø HR</p>
            <p className="text-lg font-semibold text-[var(--color-text-base)]">{hr.avg_hr}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-[var(--color-text-muted)]">Max HR</p>
            <p className="text-lg font-semibold text-[var(--color-text-base)]">{hr.max_hr}</p>
          </div>
          {hr.hr_drift_pct != null && (
            <div className="text-center">
              <p className="text-xs text-[var(--color-text-muted)]">HR-Drift</p>
              <p className="text-lg font-semibold text-[var(--color-text-base)]">
                {hr.hr_drift_pct > 0 ? '+' : ''}
                {hr.hr_drift_pct}%
              </p>
            </div>
          )}
        </div>

        {hr.hr_drift_label && (
          <div className="mb-3">
            <Badge
              variant={hr.hr_drift_pct != null && hr.hr_drift_pct < 5 ? 'success' : 'warning'}
              size="xs"
            >
              {hr.hr_drift_label}
            </Badge>
          </div>
        )}

        {zones.length > 0 && (
          <div className="space-y-1">
            {zones.map(([zone, pct]) => {
              const zoneName = zone
                .replace(/^zone_\d+_/, '')
                .replace(/_/g, ' ')
                .replace(/\b\w/g, (c) => c.toUpperCase());
              return (
                <div key={zone} className="flex items-center gap-2 text-xs">
                  <span className="w-24 text-[var(--color-text-muted)]">{zoneName}</span>
                  <div className="flex-1 h-3 bg-[var(--color-bg-muted)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--color-bg-primary)] rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>
                  <span className="w-10 text-right font-medium text-[var(--color-text-base)]">
                    {pct.toFixed(0)}%
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
