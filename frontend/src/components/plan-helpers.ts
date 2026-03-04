import type { TrainingPhase } from '@/api/training-plans';

// --- Phase Type Labels ---

export const phaseTypeLabels: Record<string, string> = {
  base: 'Basis',
  build: 'Aufbau',
  peak: 'Spitze',
  taper: 'Tapering',
  transition: 'Übergang',
};

// --- Plan Helpers ---

export function getWeekNumber(planStartDate: string, weekStart: string): number {
  const planStart = new Date(planStartDate);
  const planStartMonday = new Date(planStart);
  planStartMonday.setDate(
    planStart.getDate() - planStart.getDay() + (planStart.getDay() === 0 ? -6 : 1),
  );

  const weekStartDate = new Date(weekStart);
  const diffMs = weekStartDate.getTime() - planStartMonday.getTime();
  return Math.floor(diffMs / (7 * 24 * 60 * 60 * 1000)) + 1;
}

export function getCurrentPhase(phases: TrainingPhase[], weekNumber: number): TrainingPhase | null {
  return phases.find((p) => p.start_week <= weekNumber && weekNumber <= p.end_week) ?? null;
}

export function getTotalWeeks(phases: TrainingPhase[]): number {
  if (phases.length === 0) return 0;
  return Math.max(...phases.map((p) => p.end_week));
}

export function getCurrentWeekStart(): string {
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1));
  return monday.toISOString().split('T')[0];
}
