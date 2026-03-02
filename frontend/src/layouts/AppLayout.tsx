import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Icon } from '@nordlig/components';
import { CalendarDays, LayoutDashboard, Dumbbell, TrendingUp, Settings, Zap } from 'lucide-react';
import { BottomNav } from './BottomNav';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Dumbbell },
  { to: '/analyse', label: 'Analyse', icon: TrendingUp },
  { to: '/plan', label: 'Wochenplan', icon: CalendarDays },
  { to: '/settings', label: 'Einstellungen', icon: Settings },
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav className="fixed top-0 bottom-0 left-0 z-[100] hidden w-[224px] flex-col overflow-y-auto border-r border-[var(--color-border-muted)] bg-[var(--color-bg-elevated)] shadow-[var(--shadow-sm)] lg:flex">
      {/* Logo */}
      <div className="flex items-center gap-[9px] px-5 pt-5 pb-[22px] text-[14px] font-semibold tracking-tight text-[var(--color-text-base)]">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--color-bg-primary)]">
          <Zap className="h-4 w-4 text-[var(--color-text-on-primary)]" />
        </div>
        Training Analyzer
      </div>

      {/* Section label */}
      <div className="px-5 pt-2 pb-1 text-[10.5px] font-semibold uppercase tracking-[0.9px] text-[var(--color-text-disabled)]">
        Übersicht
      </div>

      {/* Nav items */}
      {navItems.map(({ to, label, icon }) => {
        const isActive = location.pathname.startsWith(to);
        return (
          <button
            key={to}
            onClick={() => navigate(to)}
            className={`relative flex items-center gap-[var(--spacing-xs)] px-5 py-[9px] text-[13.5px] select-none transition-colors duration-150 motion-reduce:transition-none ${
              isActive
                ? 'bg-[var(--color-bg-primary-subtle)] font-medium text-[var(--color-text-primary)]'
                : 'font-normal text-[var(--color-text-muted)] hover:bg-[var(--color-bg-surface)] hover:text-[var(--color-text-base)]'
            }`}
          >
            <Icon icon={icon} size="sm" />
            {label}
            {/* Right-side active bar */}
            {isActive && (
              <span className="absolute right-0 top-1 bottom-1 w-[3px] rounded-l-sm bg-[var(--color-interactive-primary)]" />
            )}
          </button>
        );
      })}

      {/* User chip at bottom */}
      <div className="mt-auto border-t border-[var(--color-border-muted)] px-5 py-[var(--spacing-sm)]">
        <div className="flex items-center gap-[var(--spacing-xs)]">
          <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full bg-[var(--color-bg-primary)] text-[11.5px] font-semibold text-[var(--color-text-on-primary)]">
            NC
          </div>
          <div>
            <div className="text-[13px] font-medium text-[var(--color-text-base)]">
              Nils-Christian
            </div>
            <div className="text-[11px] text-[var(--color-text-muted)]">Sub-2h</div>
          </div>
        </div>
      </div>
    </nav>
  );
}

/* Mobile top bar — only visible below 900px */
function MobileTopBar() {
  return (
    <div className="fixed top-0 right-0 left-0 z-[90] flex h-[64px] items-center justify-between border-b border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-5 shadow-[var(--shadow-xs)] lg:hidden">
      <div className="flex items-center gap-2 text-[14px] font-semibold text-[var(--color-text-base)]">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--color-bg-primary)]">
          <Zap className="h-4 w-4 text-[var(--color-text-on-primary)]" />
        </div>
        Training Analyzer
      </div>
    </div>
  );
}

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-[var(--color-bg-paper)]">
      <Sidebar />
      <MobileTopBar />

      {/* Main content — offset by sidebar on desktop, topbar on mobile */}
      <main className="min-h-screen flex-1 overflow-x-hidden pt-[64px] lg:ml-[224px] lg:pt-0">
        <div className="pb-[82px] lg:pb-0">
          <Outlet />
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
