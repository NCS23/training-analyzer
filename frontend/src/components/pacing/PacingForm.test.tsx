import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { PacingForm } from './PacingForm';
import type { RaceGoal } from '@/api/goals';

const mockGoal: RaceGoal = {
  id: 1,
  title: 'HM Sub-2h',
  race_date: '2026-05-10',
  distance_km: 21.1,
  target_time_seconds: 7199,
  target_time_formatted: '1:59:59',
  target_pace_formatted: '5:41',
  is_active: true,
  days_until: 49,
  training_plan_id: null,
  training_plan_summary: null,
  created_at: '2026-03-01T00:00:00',
  updated_at: '2026-03-01T00:00:00',
};

describe('PacingForm', () => {
  it('rendert alle Formularfelder', () => {
    render(<PacingForm goals={[]} loading={false} onGenerate={vi.fn()} />);

    expect(screen.getByLabelText('Distanz (km)')).toBeDefined();
    expect(screen.getByText('Strategie')).toBeDefined();
    expect(screen.getByText('Höhenprofil')).toBeDefined();
    expect(screen.getByText('Strategie generieren')).toBeDefined();
  });

  it('zeigt Goal-Auswahl wenn aktive Ziele vorhanden', () => {
    render(<PacingForm goals={[mockGoal]} loading={false} onGenerate={vi.fn()} />);

    expect(screen.getByText('Wettkampfziel')).toBeDefined();
  });

  it('zeigt keine Goal-Auswahl ohne aktive Ziele', () => {
    const inactiveGoal = { ...mockGoal, is_active: false };
    render(<PacingForm goals={[inactiveGoal]} loading={false} onGenerate={vi.fn()} />);

    expect(screen.queryByText('Wettkampfziel')).toBeNull();
  });

  it('zeigt Fehlermeldung bei fehlender Distanz', () => {
    const onGenerate = vi.fn();
    render(<PacingForm goals={[]} loading={false} onGenerate={onGenerate} />);

    fireEvent.click(screen.getByText('Strategie generieren'));

    expect(screen.getByText(/gültige Distanz/)).toBeDefined();
    expect(onGenerate).not.toHaveBeenCalled();
  });

  it('deaktiviert Button während Laden', () => {
    render(<PacingForm goals={[]} loading={true} onGenerate={vi.fn()} />);

    const button = screen.getByText('Berechne…');
    expect(button.closest('button')?.disabled).toBe(true);
  });
});
