// minsagaExport — baut das minsaga-export.json für die App-Migration (#821).
//
// Format-Version 1, identisch zum CLI-Script scripts/export_minsaga.py:
// die minsaga-iOS-App liest die Datei im Profil über „Aus Training
// Analyzer importieren". Historische Workouts sind bewusst NICHT
// enthalten — die kommen in minsaga aus Apple Health (Import-Master).

import type { AthleteSettings } from '@/api/athlete';
import type { RaceGoal } from '@/api/goals';
import type { TrainingPlan } from '@/api/training-plans';

export interface MinsagaExport {
  version: 1;
  athlete: {
    lthr: number | null;
    resting_hr: number | null;
    max_hr: number | null;
  };
  goals: Array<{
    title: string;
    race_date: string;
    distance_km: number;
    target_time_seconds: number | null;
    is_active: boolean;
  }>;
  plans: Array<{
    name: string;
    status: string;
    start_date: string;
    end_date: string;
    goal_title: string | null;
    phases: Array<{
      name: string;
      phase_type: string;
      start_week: number;
      end_week: number;
      weekly_template: {
        days: Array<{
          day_of_week: number;
          is_rest_day: boolean;
          sessions: Array<{
            training_type: string;
            run_type: string | null;
            notes: string | null;
          }>;
        }>;
      };
    }>;
  }>;
}

/** Pure Zusammenstellung — testbar ohne API. */
export function buildMinsagaExport(
  athlete: AthleteSettings,
  goals: RaceGoal[],
  plans: TrainingPlan[],
): MinsagaExport {
  return {
    version: 1,
    athlete: {
      lthr: athlete.lthr,
      resting_hr: athlete.resting_hr,
      max_hr: athlete.max_hr,
    },
    goals: goals.map((goal) => ({
      title: goal.title,
      race_date: goal.race_date,
      distance_km: goal.distance_km,
      target_time_seconds: goal.target_time_seconds ?? null,
      is_active: goal.is_active,
    })),
    plans: plans.map((plan) => ({
      name: plan.name,
      status: plan.status,
      start_date: plan.start_date,
      end_date: plan.end_date,
      goal_title: plan.goal_summary?.title ?? null,
      phases: plan.phases.map((phase) => ({
        name: phase.name,
        phase_type: phase.phase_type,
        start_week: phase.start_week,
        end_week: phase.end_week,
        weekly_template: {
          days: (phase.weekly_template?.days ?? []).map((day) => ({
            day_of_week: day.day_of_week,
            is_rest_day: day.is_rest_day,
            sessions: day.sessions.map((session) => ({
              training_type: session.training_type,
              run_type: session.run_type ?? null,
              notes: session.notes ?? null,
            })),
          })),
        },
      })),
    })),
  };
}

/** Löst den Browser-Download der fertigen Export-Datei aus. */
export function downloadMinsagaExportFile(exportData: MinsagaExport): void {
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'minsaga-export.json';
  anchor.click();
  window.URL.revokeObjectURL(url);
}
