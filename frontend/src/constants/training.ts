import { SEGMENT_TYPES } from './taxonomy';

// Record<string, ...> allows dynamic API key lookups from API responses
export const trainingTypeLabels: Record<string, string> = {
  recovery: 'Recovery',
  easy: 'Easy Run',
  long_run: 'Long Run',
  progression: 'Progression',
  tempo: 'Tempo',
  intervals: 'Intervall',
  repetitions: 'Repetitions',
  fartlek: 'Fartlek',
  race: 'Wettkampf',
};

type BadgeVariant = 'primary' | 'primary-bold' | 'accent' | 'accent-bold' | 'neutral';

export const trainingTypeBadgeVariant: Record<string, BadgeVariant> = {
  recovery: 'neutral',
  easy: 'primary',
  long_run: 'primary-bold',
  progression: 'primary-bold',
  tempo: 'accent',
  intervals: 'accent-bold',
  repetitions: 'accent-bold',
  fartlek: 'accent',
  race: 'accent-bold',
};

export const trainingTypeOptions = Object.entries(trainingTypeLabels).map(([value, label]) => ({
  value,
  label,
}));

export const CATEGORY_LABELS: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Lauf-ABC',
};

export const categoryBadgeVariant: Record<string, BadgeVariant> = {
  push: 'accent-bold',
  pull: 'primary',
  legs: 'primary-bold',
  core: 'accent',
  cardio: 'neutral',
  drills: 'accent',
};

export const lapTypeLabels: Record<string, string> = {
  warmup: 'Warm-up',
  cooldown: 'Cool-down',
  steady: 'Steady',
  work: 'Arbeit',
  recovery_jog: 'Trab',
  rest: 'Pause',
  strides: 'Steigerung',
  drills: 'Lauf-ABC',
  // Legacy keys (pre-migration data)
  pause: 'Pause',
  interval: 'Arbeit',
  tempo: 'Steady',
  longrun: 'Steady',
  recovery: 'Trab',
  unclassified: 'Steady',
};

export const lapTypeBadgeVariant: Record<string, BadgeVariant> = {
  work: 'accent-bold',
  steady: 'accent',
  strides: 'primary-bold',
  recovery_jog: 'primary',
  warmup: 'neutral',
  cooldown: 'neutral',
  rest: 'neutral',
  drills: 'primary-bold',
  // Legacy keys
  interval: 'accent-bold',
  tempo: 'accent',
  longrun: 'accent',
  recovery: 'primary',
  pause: 'neutral',
  unclassified: 'neutral',
};

/** Only canonical types for dropdowns (no legacy keys). */
export const lapTypeOptions = SEGMENT_TYPES.map((key) => ({
  value: key,
  label: lapTypeLabels[key] ?? key,
}));

/** Short explanations for training types — shown in tooltips. */
export const trainingTypeHints: Record<string, string> = {
  recovery: 'Sehr lockerer Lauf zur aktiven Regeneration nach harten Einheiten.',
  easy: 'Lockerer Dauerlauf im Grundlagentempo — die Basis jedes Trainings.',
  long_run: 'Langer, ruhiger Lauf zum Aufbau der Grundlagenausdauer.',
  progression: 'Steigerungslauf — beginnt locker und wird zum Ende hin schneller.',
  tempo: 'Gleichmässiger Lauf an der Laktatschwelle (»angenehm hart«).',
  intervals: 'Strukturierte schnelle Abschnitte mit Trabpausen dazwischen.',
  repetitions: 'Kurze, sehr schnelle Wiederholungen (z.B. 200m/400m) mit voller Erholung.',
  fartlek: 'Fahrtspiel — freies Wechselspiel zwischen schnellem und lockerem Tempo.',
  race: 'Wettkampf oder Testwettkampf.',
};

/** Short explanations for segment/lap types — shown in tooltips. */
export const lapTypeHints: Record<string, string> = {
  warmup: 'Aufwärmphase zu Beginn des Laufs.',
  cooldown: 'Auslaufphase am Ende des Laufs.',
  steady: 'Gleichmässiger Abschnitt im Dauerlauftempo.',
  work: 'Belastungsabschnitt (z.B. Intervall oder Tempoabschnitt).',
  recovery_jog: 'Lockerer Trab zwischen Belastungen.',
  rest: 'Stehende oder gehende Pause.',
  strides: 'Kurze Steigerungsläufe (80–100m, locker beschleunigen).',
  drills: 'Lauf-ABC / Technikübungen (z.B. Kniehebelauf, Anfersen).',
  // Legacy keys
  pause: 'Stehende oder gehende Pause.',
  interval: 'Belastungsabschnitt (z.B. Intervall oder Tempoabschnitt).',
  tempo: 'Gleichmässiger Abschnitt im Dauerlauftempo.',
  longrun: 'Gleichmässiger Abschnitt im Dauerlauftempo.',
  recovery: 'Lockerer Trab zwischen Belastungen.',
  unclassified: 'Gleichmässiger Abschnitt im Dauerlauftempo.',
};
