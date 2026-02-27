import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from './test/test-utils';
import { DashboardPage } from './pages/Dashboard';
import { SessionsPage } from './pages/Sessions';
import { SettingsPage } from './pages/Settings';
import { NotFoundPage } from './pages/NotFound';

vi.mock('@/api/athlete', () => ({
  getAthleteSettings: vi.fn().mockResolvedValue({
    id: 1,
    resting_hr: null,
    max_hr: null,
    karvonen_zones: null,
  }),
  updateAthleteSettings: vi.fn(),
}));

vi.mock('@/api/training', () => ({
  listSessions: vi.fn().mockResolvedValue({ sessions: [], total: 0, page: 1, pageSize: 20 }),
}));

describe('Page stubs render correctly', () => {
  it('renders Dashboard page', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  it('renders Sessions page', async () => {
    render(<SessionsPage />);
    await waitFor(() => {
      expect(screen.getByText('Sessions')).toBeInTheDocument();
    });
  });

  it('renders Settings page', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText('Einstellungen')).toBeInTheDocument();
    });
  });

  it('renders 404 page', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Zum Dashboard')).toBeInTheDocument();
  });
});
