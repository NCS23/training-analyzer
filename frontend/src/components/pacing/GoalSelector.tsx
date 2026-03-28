import { Label, Select } from '@nordlig/components';
import type { RaceGoal } from '@/api/goals';

interface GoalSelectorProps {
  goals: RaceGoal[];
  goalId: number | null;
  onChange: (val: string | undefined) => void;
}

export function GoalSelector({ goals, goalId, onChange }: GoalSelectorProps) {
  const activeGoals = goals.filter((g) => g.is_active);
  const goalOptions = [
    { value: '', label: 'Manuell eingeben' },
    ...activeGoals.map((g) => ({
      value: String(g.id),
      label: `${g.title} — ${g.distance_km} km in ${g.target_time_formatted}`,
    })),
  ];

  return (
    <div>
      <Label>Wettkampfziel</Label>
      {activeGoals.length > 0 ? (
        <Select options={goalOptions} value={goalId ? String(goalId) : ''} onChange={onChange} />
      ) : (
        <p className="text-sm text-[var(--color-text-muted)]">
          Noch keine Ziele angelegt. Du kannst unter{' '}
          <a href="/plan/goals" className="underline text-[var(--color-text-primary)]">
            Ziele
          </a>{' '}
          ein Wettkampfziel erstellen.
        </p>
      )}
    </div>
  );
}
