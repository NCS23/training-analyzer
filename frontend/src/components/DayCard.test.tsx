import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { DayCard } from './DayCard';
import type { WeeklyPlanEntry } from '@/api/weekly-plan';

const baseEntry: WeeklyPlanEntry = {
  day_of_week: 0,
  training_type: 'running',
  template_id: null,
  template_name: null,
  is_rest_day: false,
  notes: null,
  run_details: null,
  plan_id: null,
  edited: false,
};

const noop = () => {};

describe('DayCard edited indicator', () => {
  it('renders pencil icon for generated + edited entry', () => {
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: 1, edited: true }}
        weekStart="2026-08-03"
        isToday={false}
        isExpanded={false}
        compliance={undefined}
        showCompliance={false}
        onToggleExpand={noop}
        onUpdate={noop}
        onNavigateSession={vi.fn()}
      />,
    );
    expect(screen.getByLabelText('Manuell bearbeitet')).toBeDefined();
  });

  it('does not render pencil icon for manual entry', () => {
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: null, edited: false }}
        weekStart="2026-08-03"
        isToday={false}
        isExpanded={false}
        compliance={undefined}
        showCompliance={false}
        onToggleExpand={noop}
        onUpdate={noop}
        onNavigateSession={vi.fn()}
      />,
    );
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });

  it('does not render pencil icon for generated + unedited entry', () => {
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: 1, edited: false }}
        weekStart="2026-08-03"
        isToday={false}
        isExpanded={false}
        compliance={undefined}
        showCompliance={false}
        onToggleExpand={noop}
        onUpdate={noop}
        onNavigateSession={vi.fn()}
      />,
    );
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });
});
