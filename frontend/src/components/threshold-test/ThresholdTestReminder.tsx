import { useNavigate } from 'react-router-dom';
import { Button } from '@nordlig/components';
import { Activity, X } from 'lucide-react';
import { useThresholdReminder, type ReminderStatus } from '@/hooks/useThresholdReminder';

const REMINDER_CONFIG: Record<
  Exclude<ReminderStatus, 'fresh'>,
  { bg: string; text: string; title: string; message: string }
> = {
  never_tested: {
    bg: 'bg-[var(--color-bg-primary-subtle)]',
    text: 'text-[var(--color-text-primary)]',
    title: 'Schwellentest empfohlen',
    message: 'Führe einen 30-Min-Schwellentest durch, um deine HR-Zonen präzise zu bestimmen.',
  },
  due: {
    bg: 'bg-[var(--color-bg-warning-subtle)]',
    text: 'text-[var(--color-text-warning)]',
    title: 'Schwellentest fällig',
    message: 'Dein letzter Schwellentest liegt über 6 Wochen zurück. Zeit für einen neuen Test!',
  },
  overdue: {
    bg: 'bg-[var(--color-bg-error-subtle)]',
    text: 'text-[var(--color-text-error)]',
    title: 'Schwellentest überfällig',
    message:
      'Dein letzter Schwellentest liegt über 8 Wochen zurück. Deine HR-Zonen sind wahrscheinlich nicht mehr aktuell.',
  },
};

/**
 * Dashboard-Banner für Schwellentest-Erinnerung.
 * Zeigt Hinweis wenn kein Test vorhanden oder Test veraltet ist.
 * Kann für 1 Woche dismissed werden.
 */
export function ThresholdTestReminder() {
  const navigate = useNavigate();
  const { status, daysSinceTest, loading, dismissed, dismiss } = useThresholdReminder();

  if (loading || dismissed || status === 'fresh') return null;

  const config = REMINDER_CONFIG[status];

  return (
    <div
      className={`flex items-start gap-3 rounded-[var(--radius-component-md)] px-4 py-3 ${config.bg}`}
    >
      <Activity className={`w-4 h-4 mt-0.5 shrink-0 ${config.text}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-semibold ${config.text}`}>{config.title}</p>
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
          {config.message}
          {daysSinceTest !== null && <span className="ml-1">(vor {daysSinceTest} Tagen)</span>}
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-2 -ml-2"
          onClick={() => navigate('/profile')}
        >
          Zum Schwellentest →
        </Button>
      </div>
      <button
        type="button"
        onClick={dismiss}
        className="shrink-0 p-1 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-surface-alt)] transition-colors motion-reduce:transition-none"
        aria-label="Erinnerung ausblenden"
      >
        <X className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
      </button>
    </div>
  );
}
