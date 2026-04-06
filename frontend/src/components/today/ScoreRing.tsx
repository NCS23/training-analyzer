/**
 * ScoreRing — kreisförmiger Fitness-Score Gauge (SVG).
 *
 * Zeigt den Score 0-100 als farbigen Kreisbogen mit Zahl im Zentrum.
 * Farbe basiert auf Score-Wert: rot → orange → gelb → grün.
 */

interface Props {
  score: number;
  size?: number;
}

function scoreColor(score: number): string {
  if (score >= 75) return 'var(--color-text-success)';
  if (score >= 50) return 'var(--color-text-warning)';
  if (score >= 25) return 'var(--color-interactive-primary)';
  return 'var(--color-text-error)';
}

export function ScoreRing({ score, size = 140 }: Props) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score)) / 100;
  const dashOffset = circumference * (1 - progress);
  const center = size / 2;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
        aria-hidden="true"
      >
        {/* Hintergrund-Ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-border-default)"
          strokeWidth={strokeWidth}
          opacity={0.3}
        />
        {/* Score-Ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={scoreColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-[stroke-dashoffset] duration-700 ease-out motion-reduce:transition-none"
        />
      </svg>
      {/* Zahl im Zentrum */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-4xl font-bold tabular-nums text-[var(--color-text-base)]"
          aria-label={`Fitness-Score: ${score} von 100`}
        >
          {score}
        </span>
        <span className="text-xs text-[var(--color-text-muted)] -mt-1">von 100</span>
      </div>
    </div>
  );
}
