/** Plan-bezogene Konstanten — Single Source of Truth. */

export const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'] as const;

export const RUN_TYPE_LABELS: Record<string, string> = {
  recovery: 'Regeneration',
  easy: 'Lockerer Lauf',
  long_run: 'Langer Lauf',
  progression: 'Steigerungslauf',
  tempo: 'Tempolauf',
  intervals: 'Intervalle',
  repetitions: 'Repetitions',
  fartlek: 'Fahrtspiel',
  race: 'Wettkampf',
};

export const SESSION_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
];
