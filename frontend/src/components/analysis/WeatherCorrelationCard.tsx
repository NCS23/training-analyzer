import { useEffect, useState } from 'react';
import { Card, CardHeader, CardBody } from '@nordlig/components';
import { Cloud, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import type { WeatherCorrelationResponse, TrendInsight } from '@/api/trends';
import { getWeatherCorrelation } from '@/api/trends';

function formatPace(sec: number): string {
  const min = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${min}:${String(s).padStart(2, '0')}`;
}

function insightIcon(type: TrendInsight['type']) {
  const cls = 'w-4 h-4 shrink-0';
  if (type === 'positive')
    return <CheckCircle2 className={`${cls} text-[var(--color-text-success)]`} />;
  if (type === 'warning')
    return <AlertTriangle className={`${cls} text-[var(--color-text-warning)]`} />;
  return <Info className={`${cls} text-[var(--color-text-muted)]`} />;
}

export function WeatherCorrelationCard() {
  const [data, setData] = useState<WeatherCorrelationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWeatherCorrelation(90)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Card elevation="raised">
        <CardBody>
          <div className="text-sm text-[var(--color-text-muted)] text-center py-4">
            Lade Wetter-Korrelation...
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!data || data.data_points.length === 0) {
    return null; // Keine Daten → nichts anzeigen
  }

  const conditions = Object.entries(data.avg_pace_by_condition).sort(([, a], [, b]) => a - b);

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Cloud className="w-4 h-4 text-[var(--color-text-muted)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Wetter & Leistung</h2>
          <span className="text-xs text-[var(--color-text-muted)]">
            ({data.data_points.length} Sessions)
          </span>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          {/* Insights */}
          {data.insights.length > 0 && (
            <div className="space-y-2">
              {data.insights.map((insight, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  {insightIcon(insight.type)}
                  <span className="text-[var(--color-text-base)]">{insight.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Pace pro Wetterbedingung */}
          {conditions.length > 1 && (
            <div>
              <h3 className="text-xs font-semibold text-[var(--color-text-muted)] mb-2 uppercase tracking-wider">
                Ø Pace nach Wetter
              </h3>
              <div className="space-y-1.5">
                {conditions.map(([label, pace]) => (
                  <div key={label} className="flex items-center justify-between text-sm">
                    <span className="text-[var(--color-text-muted)]">{label}</span>
                    <span className="font-medium text-[var(--color-text-base)]">
                      {formatPace(pace)} /km
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
