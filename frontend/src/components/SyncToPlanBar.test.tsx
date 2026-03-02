import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { SyncToPlanBar } from './SyncToPlanBar';

vi.mock('@/api/weekly-plan', () => ({
  syncToPlan: vi.fn(),
}));

import { syncToPlan } from '@/api/weekly-plan';

const defaultProps = {
  planId: 1,
  weekStart: '2026-09-07',
  editedCount: 3,
  onSynced: vi.fn(),
  onDismiss: vi.fn(),
};

describe('SyncToPlanBar', () => {
  it('renders with correct edit count', () => {
    render(<SyncToPlanBar {...defaultProps} />);
    expect(screen.getByText(/3 bearbeitete Einträge/)).toBeDefined();
  });

  it('renders singular text for 1 edited entry', () => {
    render(<SyncToPlanBar {...defaultProps} editedCount={1} />);
    expect(screen.getByText(/1 bearbeiteter Eintrag/)).toBeDefined();
  });

  it('calls onDismiss when "Nur lokal" is clicked', () => {
    const onDismiss = vi.fn();
    render(<SyncToPlanBar {...defaultProps} onDismiss={onDismiss} />);
    fireEvent.click(screen.getByText('Nur lokal'));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('calls syncToPlan API and onSynced on success', async () => {
    const onSynced = vi.fn();
    vi.mocked(syncToPlan).mockResolvedValueOnce({
      phase_id: 1,
      phase_name: 'Build',
      week_key: '1',
      apply_to_all_weeks: false,
      synced_days: 3,
    });

    render(<SyncToPlanBar {...defaultProps} onSynced={onSynced} />);
    fireEvent.click(screen.getByText('Übernehmen'));

    await waitFor(() => {
      expect(syncToPlan).toHaveBeenCalledWith({
        week_start: '2026-09-07',
        plan_id: 1,
        apply_to_all_weeks: false,
      });
    });
    await waitFor(() => {
      expect(onSynced).toHaveBeenCalledOnce();
    });
  });

  it('sends apply_to_all_weeks=true when checkbox is checked', async () => {
    vi.mocked(syncToPlan).mockResolvedValueOnce({
      phase_id: 1,
      phase_name: 'Build',
      week_key: '1',
      apply_to_all_weeks: true,
      synced_days: 3,
    });

    render(<SyncToPlanBar {...defaultProps} />);

    // Click the checkbox
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    // Click sync
    fireEvent.click(screen.getByText('Übernehmen'));

    await waitFor(() => {
      expect(syncToPlan).toHaveBeenCalledWith({
        week_start: '2026-09-07',
        plan_id: 1,
        apply_to_all_weeks: true,
      });
    });
  });
});
