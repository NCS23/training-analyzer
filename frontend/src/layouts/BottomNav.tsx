import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Dumbbell, TrendingUp, Weight, Settings } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Dumbbell },
  { to: '/trends', label: 'Trends', icon: TrendingUp },
  { to: '/strength/progression', label: 'Kraft', icon: Weight },
  { to: '/settings', label: 'Einstellungen', icon: Settings },
];

export function BottomNav() {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-1 py-2 min-w-[64px] min-h-[48px] text-[10px] transition-colors ${
                isActive
                  ? 'text-[color:var(--color-interactive-primary)] font-medium'
                  : 'text-[var(--color-text-muted)]'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
