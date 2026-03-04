import { Outlet, NavLink, useLocation } from 'react-router-dom';

/* ------------------------------------------------------------------ */
/*  PlanLayout                                                         */
/* ------------------------------------------------------------------ */

const tabs = [
  { to: '/plan', label: 'Woche', end: true },
  { to: '/plan/goals', label: 'Ziele', end: false },
  { to: '/plan/programs', label: 'Programme', end: false },
  { to: '/plan/templates', label: 'Vorlagen', end: false },
  { to: '/plan/exercises', label: 'Übungen', end: false },
];

/** Hub paths where the shared header + tab bar are visible. */
const hubPaths = new Set(tabs.map((t) => t.to));

export function PlanLayout() {
  const location = useLocation();
  const isHub = hubPaths.has(location.pathname);

  if (!isHub) {
    // Detail page (e.g. /plan/programs/123) — render child only, no header/tabs
    return <Outlet />;
  }

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      <header className="pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">Plan</h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Wochenplan, Ziele, Programme und Vorlagen verwalten.
        </p>
      </header>

      {/* NavLink-based tab bar — styled like Nordlig underline tabs */}
      <nav
        className="-mb-px flex items-center overflow-x-auto border-b border-[var(--color-border-muted)]"
        aria-label="Plan-Navigation"
      >
        {tabs.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `whitespace-nowrap px-3 pb-2 text-sm font-medium transition-colors duration-150 motion-reduce:transition-none ${
                isActive
                  ? 'border-b-2 border-[var(--color-interactive-primary)] text-[var(--color-text-primary)]'
                  : 'border-b-2 border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-base)]'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
