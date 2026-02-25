export const mockRunningSession = {
  id: 1,
  date: '2024-03-15',
  workout_type: 'running' as const,
  subtype: 'interval',
  duration_sec: 3600,
  distance_km: 10.5,
  pace: '5:43',
  hr_avg: 155,
  hr_max: 178,
  hr_min: 120,
};

export const mockStrengthSession = {
  id: 2,
  date: '2024-03-16',
  workout_type: 'strength' as const,
  subtype: 'knee_dominant',
  duration_sec: 2700,
  distance_km: undefined,
  pace: undefined,
  hr_avg: 130,
  hr_max: 160,
  hr_min: 90,
};

export const mockLaps = [
  {
    lap_number: 1,
    duration_formatted: '05:00',
    distance_km: 1.0,
    pace_formatted: '5:00',
    avg_hr_bpm: 140,
    avg_cadence_spm: 170,
    suggested_type: 'warmup' as const,
    confidence: 'high' as const,
  },
  {
    lap_number: 2,
    duration_formatted: '03:30',
    distance_km: 0.8,
    pace_formatted: '4:23',
    avg_hr_bpm: 165,
    avg_cadence_spm: 180,
    suggested_type: 'interval' as const,
    confidence: 'high' as const,
  },
];

export const mockHRZones = {
  zone_1_recovery: { seconds: 600, percentage: 33.3, label: '< 150 bpm' },
  zone_2_base: { seconds: 600, percentage: 33.3, label: '150-160 bpm' },
  zone_3_tempo: { seconds: 600, percentage: 33.3, label: '> 160 bpm' },
};
