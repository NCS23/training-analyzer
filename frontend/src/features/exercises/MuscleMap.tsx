import { useState } from 'react';

import { OUTLINE_FRONT, OUTLINE_BACK, FRONT_PATHS, BACK_PATHS } from './muscleMapPaths';

/**
 * Anatomical muscle map using professional SVG paths from
 * react-native-body-highlighter (MIT License).
 *
 * Front viewBox: 0 0 724 1448
 * Back viewBox:  724 0 724 1448
 *
 * Uses `currentColor` + low opacity for the silhouette,
 * colored overlays for active muscle groups.
 */

interface MuscleMapProps {
  primaryMuscles: string[];
  secondaryMuscles: string[];
  className?: string;
}

/** Maps exercise-db muscle names to library slug + German label */
const MUSCLE_MAP: Record<string, { slug: string; label: string }> = {
  chest: { slug: 'chest', label: 'Brust' },
  shoulders: { slug: 'deltoids', label: 'Schultern' },
  biceps: { slug: 'biceps', label: 'Bizeps' },
  forearms: { slug: 'forearm', label: 'Unterarme' },
  abdominals: { slug: 'abs', label: 'Bauch' },
  obliques: { slug: 'obliques', label: 'Schräge Bauchmuskulatur' },
  quadriceps: { slug: 'quadriceps', label: 'Quadrizeps' },
  adductors: { slug: 'adductors', label: 'Adduktoren' },
  calves: { slug: 'calves', label: 'Waden' },
  neck: { slug: 'neck', label: 'Nacken' },
  traps: { slug: 'trapezius', label: 'Trapezius' },
  lats: { slug: 'upper-back', label: 'Latissimus' },
  'middle back': { slug: 'upper-back', label: 'Mittlerer Rücken' },
  'lower back': { slug: 'lower-back', label: 'Unterer Rücken' },
  triceps: { slug: 'triceps', label: 'Trizeps' },
  glutes: { slug: 'gluteal', label: 'Gesäß' },
  hamstrings: { slug: 'hamstring', label: 'Beinbeuger' },
};

function getPathsForView(muscleName: string, view: 'front' | 'back'): string[] {
  const mapping = MUSCLE_MAP[muscleName];
  if (!mapping) return [];
  const pathMap = view === 'front' ? FRONT_PATHS : BACK_PATHS;
  return pathMap[mapping.slug] ?? [];
}

function hasMusclesInView(muscles: string[], view: 'front' | 'back'): boolean {
  return muscles.some((m) => getPathsForView(m, view).length > 0);
}

function MusclePath({
  d,
  fillColor,
  opacity,
  isHovered,
  onHover,
}: {
  d: string;
  fillColor: string;
  opacity: number;
  isHovered: boolean;
  onHover: () => void;
}) {
  return (
    <path
      d={d}
      fill={fillColor}
      opacity={opacity}
      stroke={isHovered ? 'currentColor' : 'none'}
      strokeWidth={isHovered ? 3 : 0}
      strokeOpacity={0.4}
      className="cursor-pointer transition-opacity duration-200 motion-reduce:transition-none"
      onMouseEnter={onHover}
    />
  );
}

function BodyView({
  view,
  primaryMuscles,
  secondaryMuscles,
  hoveredMuscle,
  onHover,
}: {
  view: 'front' | 'back';
  primaryMuscles: string[];
  secondaryMuscles: string[];
  hoveredMuscle: string | null;
  onHover: (muscle: string | null) => void;
}) {
  const outline = view === 'front' ? OUTLINE_FRONT : OUTLINE_BACK;
  const viewBox = view === 'front' ? '0 0 724 1448' : '724 0 724 1448';

  const allMuscles = [...new Set([...primaryMuscles, ...secondaryMuscles])];

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox={viewBox}
        className="w-full max-w-[120px] h-auto"
        role="img"
        aria-label={`Muskelgruppen ${view === 'front' ? 'Vorderansicht' : 'Rückansicht'}`}
        onMouseLeave={() => onHover(null)}
      >
        {/* Body silhouette */}
        <path
          d={outline}
          fill="currentColor"
          fillOpacity={0.06}
          stroke="currentColor"
          strokeOpacity={0.18}
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Muscle highlights */}
        {allMuscles.map((muscleKey) => {
          const paths = getPathsForView(muscleKey, view);
          if (paths.length === 0) return null;

          const isPrimary = primaryMuscles.includes(muscleKey);
          const isHovered = hoveredMuscle === muscleKey;

          const fillColor = isPrimary
            ? 'var(--color-status-error, #ef4444)'
            : 'var(--color-status-warning, #f59e0b)';
          const opacity = isHovered ? 0.75 : isPrimary ? 0.5 : 0.3;

          return paths.map((path, pathIdx) => (
            <MusclePath
              key={`${muscleKey}-${pathIdx}`}
              d={path}
              fillColor={fillColor}
              opacity={opacity}
              isHovered={isHovered}
              onHover={() => onHover(muscleKey)}
            />
          ));
        })}
      </svg>
      <span className="text-xs text-[var(--color-text-muted)] mt-1">
        {view === 'front' ? 'Vorne' : 'Hinten'}
      </span>
    </div>
  );
}

export function MuscleMap({ primaryMuscles, secondaryMuscles, className }: MuscleMapProps) {
  const [hoveredMuscle, setHoveredMuscle] = useState<string | null>(null);

  const hoveredLabel = hoveredMuscle ? MUSCLE_MAP[hoveredMuscle]?.label : null;
  const isPrimaryHover = hoveredMuscle ? primaryMuscles.includes(hoveredMuscle) : false;

  const allMuscles = [...primaryMuscles, ...secondaryMuscles];
  const hasFront = hasMusclesInView(allMuscles, 'front');
  const hasBack = hasMusclesInView(allMuscles, 'back');

  return (
    <div className={className}>
      <div className="flex justify-center gap-8">
        {(hasFront || !hasBack) && (
          <BodyView
            view="front"
            primaryMuscles={primaryMuscles}
            secondaryMuscles={secondaryMuscles}
            hoveredMuscle={hoveredMuscle}
            onHover={setHoveredMuscle}
          />
        )}
        {hasBack && (
          <BodyView
            view="back"
            primaryMuscles={primaryMuscles}
            secondaryMuscles={secondaryMuscles}
            hoveredMuscle={hoveredMuscle}
            onHover={setHoveredMuscle}
          />
        )}
      </div>

      {/* Hover tooltip */}
      <div className="text-center mt-3 h-5" aria-live="polite">
        {hoveredLabel && (
          <span
            className={`text-xs font-medium ${
              isPrimaryHover
                ? 'text-[var(--color-status-error)]'
                : 'text-[var(--color-status-warning)]'
            }`}
          >
            {hoveredLabel} ({isPrimaryHover ? 'primär' : 'sekundär'})
          </span>
        )}
      </div>
    </div>
  );
}
