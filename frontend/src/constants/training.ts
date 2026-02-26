export const trainingTypeLabels: Record<string, string> = {
  recovery: 'Recovery',
  easy: 'Easy Run',
  long_run: 'Long Run',
  tempo: 'Tempo',
  intervals: 'Intervall',
  race: 'Wettkampf',
  hill_repeats: 'Bergsprints',
};

export const trainingTypeBadgeVariant: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
  recovery: 'info',
  easy: 'success',
  long_run: 'success',
  tempo: 'warning',
  intervals: 'error',
  race: 'error',
  hill_repeats: 'warning',
};

export const trainingTypeOptions = Object.entries(trainingTypeLabels).map(([value, label]) => ({
  value,
  label,
}));

export const lapTypeLabels: Record<string, string> = {
  warmup: 'Warm-up',
  interval: 'Intervall',
  pause: 'Pause',
  tempo: 'Tempo',
  longrun: 'Long Run',
  cooldown: 'Cool-down',
  recovery: 'Recovery',
  unclassified: 'Unklassifiziert',
};

export const lapTypeOptions = Object.entries(lapTypeLabels).map(([value, label]) => ({
  value,
  label,
}));
