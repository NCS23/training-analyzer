import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { PlanSuggestionCard, type PlanSuggestion } from './PlanSuggestionCard';

vi.mock('@/api/chat', async () => {
  const actual = await vi.importActual('@/api/chat');
  return {
    ...actual,
    applyPlanChange: vi.fn(),
  };
});

import { applyPlanChange } from '@/api/chat';

describe('PlanSuggestionCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders run_details intervals as a segment list', () => {
    const suggestion: PlanSuggestion = {
      action: 'replace',
      day: 'Mittwoch',
      date: '2026-05-06',
      description: 'Intervalltraining 5×800m',
      reason: 'Tempotraining',
      training_type: 'running',
      run_details: {
        run_type: 'intervals',
        target_duration_minutes: 45,
        intervals: [
          { type: 'warmup', duration_minutes: 10 },
          {
            type: 'work',
            duration_minutes: 3,
            target_pace_min: '4:25',
            target_pace_max: '4:35',
            repeats: 5,
          },
          { type: 'recovery_jog', duration_minutes: 2, repeats: 4 },
          { type: 'cooldown', duration_minutes: 8 },
        ],
      },
    };

    render(<PlanSuggestionCard suggestion={suggestion} />);

    expect(screen.getByText('Warmup')).toBeDefined();
    expect(screen.getByText('5× Belastung')).toBeDefined();
    expect(screen.getByText('4× Trab-Pause')).toBeDefined();
    expect(screen.getByText('Cooldown')).toBeDefined();
    expect(screen.getByText(/4:25–4:35\/km/)).toBeDefined();
  });

  it('forwards run_details to applyPlanChange when applying', async () => {
    vi.mocked(applyPlanChange).mockResolvedValueOnce({
      success: true,
      message: 'ok',
    });

    const suggestion: PlanSuggestion = {
      action: 'add',
      day: 'Freitag',
      date: '2026-05-08',
      description: 'Tempo-Lauf',
      reason: 'Schwellentempo',
      training_type: 'running',
      run_details: {
        run_type: 'tempo',
        intervals: [{ type: 'steady', duration_minutes: 25 }],
      },
    };

    render(<PlanSuggestionCard suggestion={suggestion} />);
    fireEvent.click(screen.getByRole('button', { name: /Übernehmen/ }));

    await waitFor(() => {
      expect(applyPlanChange).toHaveBeenCalledTimes(1);
    });
    const call = vi.mocked(applyPlanChange).mock.calls[0][0];
    expect(call.training_type).toBe('running');
    expect(call.run_details?.run_type).toBe('tempo');
    expect(call.run_details?.intervals).toHaveLength(1);
  });

  it('renders without run_details (legacy text-only suggestion)', () => {
    const suggestion: PlanSuggestion = {
      action: 'rest_day',
      day: 'Sonntag',
      date: '2026-05-10',
      description: 'Ruhetag',
      reason: 'Hohe Belastung',
    };

    render(<PlanSuggestionCard suggestion={suggestion} />);
    expect(screen.getByText('Ruhetag einschieben')).toBeDefined();
    expect(screen.queryByText('Warmup')).toBeNull();
  });
});
