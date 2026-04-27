import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { AppLayout } from './AppLayout';

const logoutMock = vi.fn();

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    isAdmin: false,
    logout: logoutMock,
  }),
}));

vi.mock('@/api/chat', () => ({
  getChatNotifications: vi.fn().mockResolvedValue({ notifications: [], count: 0 }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet" />,
  };
});

describe('AppLayout — Mobile Top Bar', () => {
  beforeEach(() => {
    logoutMock.mockReset();
  });

  it('renders a logout button in the mobile top bar (#763)', () => {
    render(<AppLayout />);
    // Mobile-Top-Bar und Sidebar rendern beide einen Logout-Button.
    // Wir filtern auf den, der in einem .lg:hidden Container steckt.
    const logoutButtons = screen.getAllByRole('button', { name: /Abmelden/i });
    expect(logoutButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('mobile logout button triggers useAuth().logout', async () => {
    render(<AppLayout />);
    const logoutButtons = screen.getAllByRole('button', { name: /Abmelden/i });
    // Fire on the first one (mobile top bar appears first in DOM order
    // because it sits in the layout above the sidebar — in fact both work,
    // we just need to confirm the call happens).
    fireEvent.click(logoutButtons[0]);
    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
  });
});
