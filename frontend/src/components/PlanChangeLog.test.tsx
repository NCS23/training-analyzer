import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { PlanChangeLog } from './PlanChangeLog';

vi.mock('@/api/training-plans', async () => {
  const actual = await vi.importActual('@/api/training-plans');
  return {
    ...actual,
    getChangelog: vi.fn(),
    updateChangelogReason: vi.fn(),
  };
});

import { getChangelog, updateChangelogReason } from '@/api/training-plans';

const MOCK_ENTRIES = [
  {
    id: 1,
    plan_id: 1,
    change_type: 'plan_created',
    category: 'meta' as const,
    summary: "Trainingsplan 'HM Sub-2h' erstellt",
    details: null,
    reason: null,
    created_by: null,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    plan_id: 1,
    change_type: 'phase_added',
    category: 'structure' as const,
    summary: "Phase 'Grundlage' hinzugefuegt (Woche 1-4)",
    details: { changed_fields: ['name'] },
    reason: 'Erste Phase',
    created_by: null,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
];

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
describe('PlanChangeLog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders changelog entries with icons and summary', async () => {
    vi.mocked(getChangelog).mockResolvedValueOnce({
      entries: MOCK_ENTRIES,
      total: 2,
    });

    render(<PlanChangeLog planId={1} />);

    // Open the collapsible
    await waitFor(() => {
      expect(screen.getByText(/Änderungshistorie/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Änderungshistorie/));

    await waitFor(() => {
      expect(screen.getByText(/HM Sub-2h/)).toBeDefined();
      expect(screen.getByText(/Grundlage/)).toBeDefined();
    });
  });

  it('expanding entry shows details', async () => {
    vi.mocked(getChangelog).mockResolvedValueOnce({
      entries: MOCK_ENTRIES,
      total: 2,
    });

    render(<PlanChangeLog planId={1} />);

    // Open collapsible
    await waitFor(() => {
      expect(screen.getByText(/Änderungshistorie/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Änderungshistorie/));

    // Click on entry with details
    await waitFor(() => {
      expect(screen.getByText(/Grundlage/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Grundlage/));

    await waitFor(() => {
      expect(screen.getByText(/Grund:/)).toBeDefined();
      expect(screen.getByText(/Erste Phase/)).toBeDefined();
    });
  });

  it('"Grund hinzufügen" opens input and saves on Enter', async () => {
    vi.mocked(getChangelog).mockResolvedValueOnce({
      entries: [MOCK_ENTRIES[0]], // Entry without reason
      total: 1,
    });
    vi.mocked(updateChangelogReason).mockResolvedValueOnce({
      ...MOCK_ENTRIES[0],
      reason: 'Neuer Grund',
    });

    render(<PlanChangeLog planId={1} />);

    // Open collapsible
    await waitFor(() => {
      expect(screen.getByText(/Änderungshistorie/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Änderungshistorie/));

    // Click on entry
    await waitFor(() => {
      expect(screen.getByText(/HM Sub-2h/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/HM Sub-2h/));

    // Click "Grund hinzufügen"
    await waitFor(() => {
      expect(screen.getByText(/Grund hinzufügen/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Grund hinzufügen/));

    // Type reason and press Enter
    const input = screen.getByPlaceholderText('Grund eingeben...');
    fireEvent.change(input, { target: { value: 'Neuer Grund' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(updateChangelogReason).toHaveBeenCalledWith(1, 1, 'Neuer Grund');
    });
  });

  it('"Mehr laden" button calls API with offset', async () => {
    vi.mocked(getChangelog)
      .mockResolvedValueOnce({
        entries: MOCK_ENTRIES,
        total: 5, // More than PAGE_SIZE entries exist
      })
      .mockResolvedValueOnce({
        entries: [
          {
            id: 3,
            plan_id: 1,
            change_type: 'plan_updated',
            category: 'meta' as const,
            summary: 'Plan aktualisiert',
            details: null,
            reason: null,
            created_by: null,
            created_at: new Date(Date.now() - 7200000).toISOString(),
          },
        ],
        total: 5,
      });

    render(<PlanChangeLog planId={1} />);

    // Open collapsible
    await waitFor(() => {
      expect(screen.getByText(/Änderungshistorie/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Änderungshistorie/));

    // Click "Mehr laden"
    await waitFor(() => {
      expect(screen.getByText('Mehr laden')).toBeDefined();
    });
    fireEvent.click(screen.getByText('Mehr laden'));

    await waitFor(() => {
      expect(getChangelog).toHaveBeenCalledWith(1, 20, 2, undefined); // offset=2 (existing entries)
    });
  });

  it('shows empty state when no entries', async () => {
    vi.mocked(getChangelog).mockResolvedValueOnce({
      entries: [],
      total: 0,
    });

    render(<PlanChangeLog planId={1} />);

    // Open collapsible
    await waitFor(() => {
      expect(screen.getByText(/Änderungshistorie/)).toBeDefined();
    });
    fireEvent.click(screen.getByText(/Änderungshistorie/));

    await waitFor(() => {
      expect(screen.getByText(/Noch keine Änderungen/)).toBeDefined();
    });
  });
});
