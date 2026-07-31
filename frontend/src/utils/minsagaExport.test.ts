// minsagaExport.test — Format-Version 1 muss stabil bleiben (#821):
// die minsaga-iOS-App parst genau diese Struktur.

import { describe, expect, it } from 'vitest';
import { buildMinsagaExport } from './minsagaExport';
import type { AthleteSettings } from '@/api/athlete';
import type { RaceGoal } from '@/api/goals';
import type { TrainingPlan } from '@/api/training-plans';

const athlete = {
  lthr: 172,
  resting_hr: 48,
  max_hr: 191,
} as AthleteSettings;

const goal = {
  title: 'Halbmarathon Hamburg',
  race_date: '2026-11-05',
  distance_km: 21.0975,
  target_time_seconds: 7140,
  is_active: true,
} as RaceGoal;

const plan = {
  name: 'HM Sub 2h',
  status: 'active',
  start_date: '2026-08-03',
  end_date: '2026-11-01',
  goal_summary: { id: 1, title: 'Halbmarathon Hamburg' },
  phases: [
    {
      name: 'Base',
      phase_type: 'base',
      start_week: 1,
      end_week: 6,
      weekly_template: {
        days: [
          {
            day_of_week: 2,
            is_rest_day: false,
            sessions: [{ training_type: 'running', run_type: 'easy', notes: 'locker' }],
          },
          { day_of_week: 1, is_rest_day: true, sessions: [] },
        ],
      },
    },
  ],
} as unknown as TrainingPlan;

describe('buildMinsagaExport (#821)', () => {
  it('baut Format-Version 1 mit athlete, goals und plans', () => {
    const result = buildMinsagaExport(athlete, [goal], [plan]);

    expect(result.version).toBe(1);
    expect(result.athlete).toEqual({ lthr: 172, resting_hr: 48, max_hr: 191 });
    expect(result.goals).toEqual([
      {
        title: 'Halbmarathon Hamburg',
        race_date: '2026-11-05',
        distance_km: 21.0975,
        target_time_seconds: 7140,
        is_active: true,
      },
    ]);
    expect(result.plans[0]).toMatchObject({
      name: 'HM Sub 2h',
      status: 'active',
      goal_title: 'Halbmarathon Hamburg',
    });
    expect(result.plans[0].phases[0].weekly_template.days).toHaveLength(2);
    expect(result.plans[0].phases[0].weekly_template.days[0].sessions[0]).toEqual({
      training_type: 'running',
      run_type: 'easy',
      notes: 'locker',
    });
  });

  it('übersteht Plan ohne Ziel und Phase ohne Template', () => {
    const kahlerPlan = {
      name: 'Leer',
      status: 'draft',
      start_date: '2026-01-01',
      end_date: '2026-02-01',
      goal_summary: null,
      phases: [
        { name: 'P1', phase_type: 'base', start_week: 1, end_week: 4, weekly_template: null },
      ],
    } as unknown as TrainingPlan;

    const result = buildMinsagaExport(athlete, [], [kahlerPlan]);

    expect(result.plans[0].goal_title).toBeNull();
    expect(result.plans[0].phases[0].weekly_template.days).toEqual([]);
  });
});
