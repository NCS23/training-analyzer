import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Dumbbell, Settings } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Dumbbell },
  { to: '/settings', label: 'Einstellungen', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-60 sticky top-0 h-screen border-r border-[var(--color-sidebar-border)] bg-[var(--color-sidebar-bg)]">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-14 border-b border-[var(--color-sidebar-border)]">
        <Dumbbell className="w-5 h-5 text-[color:var(--color-interactive-primary)]" />
        <span className="text-sm font-semibold text-[var(--color-text-base)] tracking-tight">
          Training Analyzer
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-component-md)] text-sm transition-colors min-h-[44px] ${
                isActive
                  ? 'bg-[var(--color-sidebar-item-active)] text-[var(--color-sidebar-text-active)] font-medium'
                  : 'text-[var(--color-sidebar-text)] hover:bg-[var(--color-sidebar-item-hover)] hover:text-[var(--color-text-base)]'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
