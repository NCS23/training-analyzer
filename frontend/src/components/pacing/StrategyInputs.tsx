import { Label, Select } from '@nordlig/components';
import type { ElevationSegment, PacingRecommendationResponse } from '@/api/pacing';
import { ElevationProfile } from './ElevationProfile';
import { RecommendButton, RecommendReasoning } from './RecommendButton';

type Strategy = 'even' | 'negative' | 'effort_based';
type ElevationPreset = 'flat' | 'rolling' | 'hilly';

const STRATEGY_OPTIONS = [
  { value: 'even', label: 'Gleichmäßig (Even Split)' },
  { value: 'negative', label: 'Negative Splits' },
  { value: 'effort_based', label: 'Effort-Based (konstante Belastung)' },
];

const ELEVATION_OPTIONS = [
  { value: 'flat', label: 'Flach' },
  { value: 'rolling', label: 'Wellig (~15m/km)' },
  { value: 'hilly', label: 'Hügelig (~30m/km)' },
];

interface StrategyInputsProps {
  strategy: Strategy;
  elevationPreset: ElevationPreset;
  elevationSegments: ElevationSegment[] | null;
  raceName: string;
  distanceKm: number | null;
  targetTimeSeconds: number | null;
  reasoning: string | null;
  disabled?: boolean;
  onStrategyChange: (val: Strategy) => void;
  onElevationChange: (val: ElevationPreset) => void;
  onElevationSegmentsChange: (segments: ElevationSegment[] | null) => void;
  onRecommendation: (rec: PacingRecommendationResponse) => void;
  onReasoningClose: () => void;
}

export function StrategyInputs({
  strategy,
  elevationPreset,
  elevationSegments,
  raceName,
  distanceKm,
  targetTimeSeconds,
  reasoning,
  disabled,
  onStrategyChange,
  onElevationChange,
  onElevationSegmentsChange,
  onRecommendation,
  onReasoningClose,
}: StrategyInputsProps) {
  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between">
            <Label>Strategie</Label>
            <RecommendButton
              raceName={raceName}
              distanceKm={distanceKm}
              targetTimeSeconds={targetTimeSeconds}
              disabled={disabled}
              onRecommendation={onRecommendation}
            />
          </div>
          <Select
            options={STRATEGY_OPTIONS}
            value={strategy}
            onChange={(val) => {
              if (val) onStrategyChange(val as Strategy);
              onReasoningClose();
            }}
          />
        </div>
        <div>
          <Label>Höhenprofil</Label>
          <Select
            options={ELEVATION_OPTIONS}
            value={elevationPreset}
            onChange={(val) => {
              if (val) onElevationChange(val as ElevationPreset);
              onElevationSegmentsChange(null);
              onReasoningClose();
            }}
            disabled={!!elevationSegments}
          />
        </div>
      </div>

      <ElevationProfile
        segments={elevationSegments}
        onSegmentsChange={onElevationSegmentsChange}
        disabled={disabled}
      />

      {reasoning && <RecommendReasoning reasoning={reasoning} onClose={onReasoningClose} />}
    </>
  );
}
