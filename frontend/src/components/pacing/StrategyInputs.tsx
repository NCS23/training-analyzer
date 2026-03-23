import { Label, Select } from '@nordlig/components';
import type { ElevationSegment, ExperienceLevel, PacingRecommendationResponse } from '@/api/pacing';
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

const EXPERIENCE_OPTIONS = [
  { value: 'beginner', label: 'Anfänger' },
  { value: 'intermediate', label: 'Fortgeschritten' },
  { value: 'advanced', label: 'Erfahren' },
];

interface StrategyInputsProps {
  strategy: Strategy;
  elevationPreset: ElevationPreset;
  elevationSegments: ElevationSegment[] | null;
  experienceLevel: ExperienceLevel;
  raceName: string;
  distanceKm: number | null;
  targetTimeSeconds: number | null;
  temperatureCelsius: number | null;
  reasoning: string | null;
  disabled?: boolean;
  onStrategyChange: (val: Strategy) => void;
  onElevationChange: (val: ElevationPreset) => void;
  onElevationSegmentsChange: (segments: ElevationSegment[] | null) => void;
  onExperienceLevelChange: (val: ExperienceLevel) => void;
  onRecommendation: (rec: PacingRecommendationResponse) => void;
  onReasoningClose: () => void;
}

export function StrategyInputs({
  strategy,
  elevationPreset,
  elevationSegments,
  experienceLevel,
  raceName,
  distanceKm,
  targetTimeSeconds,
  temperatureCelsius,
  reasoning,
  disabled,
  onStrategyChange,
  onElevationChange,
  onElevationSegmentsChange,
  onExperienceLevelChange,
  onRecommendation,
  onReasoningClose,
}: StrategyInputsProps) {
  return (
    <>
      {/* Inputs: Höhenprofil + Erfahrung (beeinflussen die Empfehlung) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
        <div>
          <Label>Erfahrung</Label>
          <Select
            options={EXPERIENCE_OPTIONS}
            value={experienceLevel}
            onChange={(val) => {
              if (val) onExperienceLevelChange(val as ExperienceLevel);
              onReasoningClose();
            }}
          />
        </div>
      </div>

      <ElevationProfile
        segments={elevationSegments}
        onSegmentsChange={onElevationSegmentsChange}
        disabled={disabled}
      />

      {/* Empfehlung: Button + Begründung */}
      <RecommendButton
        raceName={raceName}
        distanceKm={distanceKm}
        targetTimeSeconds={targetTimeSeconds}
        experienceLevel={experienceLevel}
        temperatureCelsius={temperatureCelsius}
        elevationPreset={elevationPreset}
        elevationSegments={elevationSegments}
        disabled={disabled}
        onRecommendation={onRecommendation}
      />
      {reasoning && <RecommendReasoning reasoning={reasoning} onClose={onReasoningClose} />}

      {/* Output: Strategie (wird von Empfehlung gesetzt, manuell überschreibbar) */}
      <div>
        <Label>Strategie</Label>
        <Select
          options={STRATEGY_OPTIONS}
          value={strategy}
          onChange={(val) => {
            if (val) onStrategyChange(val as Strategy);
            onReasoningClose();
          }}
        />
      </div>
    </>
  );
}
