import { useEffect, useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Icon } from '@nordlig/components';
import {
  CalendarDays,
  LayoutDashboard,
  Dumbbell,
  TrendingUp,
  User,
  ChevronDown,
  Calendar,
  Target,
  BookOpen,
  ClipboardList,
  Library,
  Bot,
} from 'lucide-react';
import { getChatNotifications } from '@/api/chat';
import { BottomNav } from './BottomNav';

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  children?: { to: string; label: string; icon: typeof LayoutDashboard; end?: boolean }[];
}

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Dumbbell },
  { to: '/analyse', label: 'Analyse', icon: TrendingUp },
  { to: '/chat', label: 'KI-Chat', icon: Bot },
  {
    to: '/plan',
    label: 'Plan',
    icon: CalendarDays,
    children: [
      { to: '/plan', label: 'Woche', icon: Calendar, end: true },
      { to: '/plan/goals', label: 'Ziele', icon: Target },
      { to: '/plan/programs', label: 'Programme', icon: BookOpen },
      { to: '/plan/templates', label: 'Vorlagen', icon: ClipboardList },
      { to: '/plan/exercises', label: 'Übungen', icon: Library },
    ],
  },
  { to: '/profile', label: 'Profil', icon: User },
];

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [planExpanded, setPlanExpanded] = useState(location.pathname.startsWith('/plan'));
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    void getChatNotifications()
      .then((res) => setNotificationCount(res.count))
      .catch(() => {});
  }, []);

  return (
    <nav className="fixed top-0 bottom-0 left-0 z-[100] hidden w-[224px] flex-col overflow-y-auto border-r border-[var(--color-border-muted)] bg-[var(--color-bg-elevated)] shadow-[var(--shadow-sm)] lg:flex">
      {/* Logo */}
      <div className="flex items-center gap-[9px] px-5 pt-5 pb-[22px] text-[14px] font-semibold tracking-tight text-[var(--color-text-base)]">
        <img src="/logo.svg" alt="Training Analyzer" className="h-10 w-10 shrink-0" />
        Training Analyzer
      </div>

      {/* Section label */}
      <div className="px-5 pt-2 pb-1 text-[10.5px] font-semibold uppercase tracking-[0.9px] text-[var(--color-text-disabled)]">
        Übersicht
      </div>

      {/* Nav items */}
      {navItems.map((item) => {
        const isActive = item.children
          ? location.pathname.startsWith(item.to)
          : location.pathname.startsWith(item.to);

        if (item.children) {
          return (
            <div key={item.to}>
              {/* Parent item with expand toggle */}
              <button
                onClick={() => {
                  if (!location.pathname.startsWith('/plan')) {
                    navigate('/plan');
                    setPlanExpanded(true);
                  } else {
                    setPlanExpanded((prev) => !prev);
                  }
                }}
                className={`relative flex w-full items-center gap-[var(--spacing-xs)] px-5 py-[9px] text-[13.5px] select-none transition-colors duration-150 motion-reduce:transition-none ${
                  isActive
                    ? 'bg-[var(--color-bg-primary-subtle)] font-medium text-[var(--color-text-primary)]'
                    : 'font-normal text-[var(--color-text-muted)] hover:bg-[var(--color-bg-surface)] hover:text-[var(--color-text-base)]'
                }`}
              >
                <Icon icon={item.icon} size="sm" />
                {item.label}
                <ChevronDown
                  className={`ml-auto h-3.5 w-3.5 transition-transform duration-150 motion-reduce:transition-none ${
                    planExpanded ? 'rotate-0' : '-rotate-90'
                  }`}
                />
                {isActive && (
                  <span className="absolute right-0 top-1 bottom-1 w-[3px] rounded-l-sm bg-[var(--color-interactive-primary)]" />
                )}
              </button>

              {/* Sub-items */}
              {planExpanded && (
                <div className="pb-1">
                  {item.children.map((child) => {
                    const childActive = child.end
                      ? location.pathname === child.to
                      : location.pathname.startsWith(child.to);
                    return (
                      <button
                        key={child.to}
                        onClick={() => navigate(child.to)}
                        className={`flex w-full items-center gap-[var(--spacing-xs)] py-[7px] pl-10 pr-5 text-[12.5px] select-none transition-colors duration-150 motion-reduce:transition-none ${
                          childActive
                            ? 'font-medium text-[var(--color-text-primary)]'
                            : 'font-normal text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
                        }`}
                      >
                        <child.icon className="h-3.5 w-3.5 shrink-0" />
                        {child.label}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        }

        const showBadge = item.to === '/chat' && notificationCount > 0 && !isActive;

        return (
          <button
            key={item.to}
            onClick={() => navigate(item.to)}
            className={`relative flex items-center gap-[var(--spacing-xs)] px-5 py-[9px] text-[13.5px] select-none transition-colors duration-150 motion-reduce:transition-none ${
              isActive
                ? 'bg-[var(--color-bg-primary-subtle)] font-medium text-[var(--color-text-primary)]'
                : 'font-normal text-[var(--color-text-muted)] hover:bg-[var(--color-bg-surface)] hover:text-[var(--color-text-base)]'
            }`}
          >
            <Icon icon={item.icon} size="sm" />
            {item.label}
            {showBadge && (
              <span className="ml-auto flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-[var(--color-interactive-primary)] text-[10px] font-semibold text-[var(--color-text-on-primary)] px-1">
                {notificationCount}
              </span>
            )}
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
        <img src="/logo.svg" alt="Training Analyzer" className="h-10 w-10 shrink-0" />
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
