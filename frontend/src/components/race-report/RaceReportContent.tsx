import { Alert, AlertDescription } from '@nordlig/components';
import type { RaceReportData, RaceAnalysis, KmSplit } from '@/api/training';
import { RaceGoalResult } from './RaceGoalResult';
import { RacePacingChart } from './RacePacingChart';
import { RacePaceConsistency } from './RacePaceConsistency';
import { RaceHRAnalysis } from './RaceHRAnalysis';
import { RaceTrainingComparison } from './RaceTrainingComparison';
import { RacePreviousRaces } from './RacePreviousRaces';
import { RaceAIAnalysis } from './RaceAIAnalysis';

interface RaceReportContentProps {
  report: RaceReportData;
  splits: KmSplit[];
  analysis: RaceAnalysis | null;
  isAnalyzing: boolean;
  onTriggerAnalysis: () => void;
}

export function RaceReportContent({
  report,
  splits,
  analysis,
  isAnalyzing,
  onTriggerAnalysis,
}: RaceReportContentProps) {
  return (
    <>
      {report.goal_comparison ? (
        <RaceGoalResult goal={report.goal_comparison} />
      ) : (
        <Alert variant="info">
          <AlertDescription>
            Kein Wettkampf-Ziel gefunden. Erstelle ein Ziel unter Plan &gt; Ziele, damit der Bericht
            Soll/Ist vergleichen kann.
          </AlertDescription>
        </Alert>
      )}

      <RacePacingChart
        splits={splits}
        pacing={report.pacing_strategy}
        targetPaceSec={report.goal_comparison?.target_pace_sec_per_km}
      />

      {report.pace_consistency && <RacePaceConsistency consistency={report.pace_consistency} />}

      {report.hr_management && <RaceHRAnalysis hr={report.hr_management} />}

      {report.training_comparison && (
        <RaceTrainingComparison comparison={report.training_comparison} />
      )}

      <RacePreviousRaces races={report.previous_races} />

      <RaceAIAnalysis analysis={analysis} isAnalyzing={isAnalyzing} onTrigger={onTriggerAnalysis} />
    </>
  );
}
