import type { PhaseType, PlanStatus, TrainingPhase } from '@/api/training-plans';

// --- Phase Type Labels ---

export const phaseTypeLabels: Record<string, string> = {
  base: 'Basis',
  build: 'Aufbau',
  peak: 'Spitze',
  taper: 'Tapering',
  transition: 'Übergang',
};

// --- Phase & Plan Constants ---

export const PHASE_TYPES: { value: PhaseType; label: string }[] = [
  { value: 'base', label: 'Grundlage' },
  { value: 'build', label: 'Aufbau' },
  { value: 'peak', label: 'Wettkampf' },
  { value: 'taper', label: 'Tapering' },
  { value: 'transition', label: 'Übergang' },
];

export const PHASE_COLORS: Record<PhaseType, 'neutral' | 'info' | 'success' | 'warning' | 'error'> = {
  base: 'neutral',
  build: 'info',
  peak: 'success',
  taper: 'warning',
  transition: 'error',
};

export const STATUS_OPTIONS: { value: PlanStatus; label: string }[] = [
  { value: 'draft', label: 'Entwurf' },
  { value: 'active', label: 'Aktiv' },
  { value: 'completed', label: 'Abgeschlossen' },
  { value: 'paused', label: 'Pausiert' },
];

export const STATUS_BADGE_VARIANTS: Record<PlanStatus, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  active: 'success',
  completed: 'info',
  paused: 'warning',
};

export const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

export function formatDateDE(d: Date | string | undefined | null): string {
  if (!d) return '—';
  const date = typeof d === 'string' ? new Date(d) : d;
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

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
