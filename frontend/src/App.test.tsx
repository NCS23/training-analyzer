import { describe, it, expect } from 'vitest';
import { render, screen } from './test/test-utils';
import { DashboardPage } from './pages/Dashboard';
import { SessionsPage } from './pages/Sessions';
import { SettingsPage } from './pages/Settings';
import { NotFoundPage } from './pages/NotFound';

describe('Page stubs render correctly', () => {
  it('renders Dashboard page', () => {
    render(<DashboardPage />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders Sessions page', () => {
    render(<SessionsPage />);
    expect(screen.getByText('Sessions')).toBeInTheDocument();
  });

  it('renders Settings page', () => {
    render(<SettingsPage />);
    expect(screen.getByText('Einstellungen')).toBeInTheDocument();
  });

  it('renders 404 page', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Zum Dashboard')).toBeInTheDocument();
  });
});
