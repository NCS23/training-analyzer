import { Card, CardBody, Progress } from '@nordlig/components';
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { FitnessScoreResponse } from '@/api/fitness';
import { ScoreRing } from './ScoreRing';

interface Props {
  data: FitnessScoreResponse;
}

const FORM_COLOR: Record<string, string> = {
  green: 'var(--color-text-success)',
  yellow: 'var(--color-text-warning)',
  orange: 'var(--color-text-error)',
};

const FORM_BG: Record<string, string> = {
  fresh: 'var(--color-bg-success-subtle)',
  fatigued: 'var(--color-bg-warning-subtle)',
};

function TrendIcon({ trend }: { trend: FitnessScoreResponse['trend'] }) {
  if (trend === 'rising')
    return <TrendingUp className="h-4 w-4 text-[var(--color-text-success)]" />;
  if (trend === 'falling')
    return <TrendingDown className="h-4 w-4 text-[var(--color-text-error)]" />;
  return <Minus className="h-4 w-4 text-[var(--color-text-muted)]" />;
}

export function ScoreSection({ data }: Props) {
  const formColor = FORM_COLOR[data.form.color] ?? 'var(--color-text-base)';
  const bgColor = FORM_BG[data.form.status];

  return (
    <section aria-label="Fitness-Score">
      <Card elevation="raised">
        <CardBody>
          <div
            className="rounded-[var(--radius-component-sm)] p-4 -m-1"
            style={bgColor ? { background: bgColor } : undefined}
          >
            {/* Hero: Ring + Status */}
            <div className="flex items-center gap-5">
              <ScoreRing score={data.score} />

              <div className="flex-1 min-w-0 space-y-2">
                <div>
                  <span className="text-base font-semibold" style={{ color: formColor }}>
                    {data.form.label}
                  </span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <TrendIcon trend={data.trend} />
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {data.trend_label}
                    </span>
                  </div>
                </div>

                {/* Sub-Scores */}
                <div className="space-y-2">
                  <SubScore label="Ausdauer" value={data.endurance_score} />
                  <SubScore label="Kraft" value={data.strength_score} />
                </div>
              </div>
            </div>
          </div>

          {/* Empfehlung */}
          <p className="mt-3 text-sm text-[var(--color-text-muted)]">{data.form.recommendation}</p>

          {/* Link zur Analyse */}
          <Link
            to="/analyse"
            className="mt-3 flex items-center gap-1.5 text-xs font-medium text-[var(--color-interactive-primary)] hover:underline"
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Detaillierte Analyse
          </Link>
        </CardBody>
      </Card>
    </section>
  );
}

function SubScore({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--color-text-muted)] w-16 shrink-0">{label}</span>
      <Progress value={value} max={100} size="sm" className="flex-1" />
      <span className="text-xs font-medium tabular-nums text-[var(--color-text-base)] w-6 text-right">
        {value}
      </span>
    </div>
  );
}
