import { Card, CardHeader, CardBody } from '@nordlig/components';
import type { HRZone } from '@/api/training';

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function fallbackZoneColor(key: string): string {
  if (key.includes('recovery') || key.includes('zone_1')) return 'var(--color-text-disabled)';
  if (key.includes('base') || key.includes('zone_2')) return 'var(--color-bg-success-solid)';
  return 'var(--color-bg-warning-solid)';
}

function ZoneBar({ zones, title }: { zones: Record<string, HRZone>; title: string }) {
  return (
    <Card elevation="raised">
      <CardHeader>
        <h2 className="text-sm font-semibold text-[var(--color-text-base)]">{title}</h2>
      </CardHeader>
      <CardBody>
        <div className="space-y-3">
          {Object.entries(zones).map(([key, zone]: [string, HRZone]) => (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[var(--color-text-muted)]">
                  {zone.name ? `${zone.name} (${zone.label})` : zone.label}
                </span>
                <span className="font-medium text-[var(--color-text-base)]">
                  {zone.percentage}%
                  {zone.seconds != null && (
                    <span className="text-[var(--color-text-muted)] ml-1">
                      ({formatDuration(zone.seconds)})
                    </span>
                  )}
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-[var(--color-bg-subtle)]">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${Math.min(zone.percentage, 100)}%`,
                    backgroundColor: zone.color ?? fallbackZoneColor(key),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

interface SessionHRZonesSectionProps {
  hrZones: Record<string, HRZone>;
  workingHrZones: Record<string, HRZone> | null;
}

export function SessionHRZonesSection({ hrZones, workingHrZones }: SessionHRZonesSectionProps) {
  return (
    <section aria-label="Herzfrequenz-Zonen">
      <div
        className={`grid gap-5 ${workingHrZones ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}
      >
        <ZoneBar zones={hrZones} title="HF-Zonen Gesamt" />
        {workingHrZones && <ZoneBar zones={workingHrZones} title="HF-Zonen Arbeitsbereich" />}
      </div>
    </section>
  );
}
