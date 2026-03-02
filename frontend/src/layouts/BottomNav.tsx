import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, TrendingUp, CalendarDays, User } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Home', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Activity },
  { to: '/analyse', label: 'Analyse', icon: TrendingUp },
  { to: '/plan', label: 'Plan', icon: CalendarDays },
  { to: '/settings', label: 'Profil', icon: User },
];

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-[200] border-t border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] pb-[env(safe-area-inset-bottom)] lg:hidden">
      <div className="flex h-[62px] items-stretch">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center justify-center gap-[3px] pt-1 text-[10px] font-medium transition-colors duration-150 motion-reduce:transition-none ${
                isActive
                  ? 'text-[var(--color-interactive-primary)]'
                  : 'text-[var(--color-text-muted)]'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
