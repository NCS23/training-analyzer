import { Link } from 'react-router-dom';
import { Alert, AlertDescription } from '@nordlig/components';
import { useThresholdReminder, type ReminderStatus } from '@/hooks/useThresholdReminder';

type AlertVariant = 'info' | 'warning' | 'error';

const REMINDER_CONFIG: Record<
  Exclude<ReminderStatus, 'fresh'>,
  { variant: AlertVariant; title: string; message: string }
> = {
  never_tested: {
    variant: 'info',
    title: 'Schwellentest empfohlen',
    message: 'Führe einen 30-Min-Schwellentest durch, um deine HR-Zonen präzise zu bestimmen.',
  },
  due: {
    variant: 'warning',
    title: 'Schwellentest fällig',
    message: 'Dein letzter Schwellentest liegt über 6 Wochen zurück. Zeit für einen neuen Test!',
  },
  overdue: {
    variant: 'error',
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
  const { status, daysSinceTest, loading, dismissed, dismiss } = useThresholdReminder();

  if (loading || dismissed || status === 'fresh') return null;

  const config = REMINDER_CONFIG[status];

  return (
    <Alert variant={config.variant} closeable onClose={dismiss}>
      <AlertDescription>
        <p className="font-semibold">{config.title}</p>
        <p className="text-xs opacity-80 mt-1">
          {config.message}
          {daysSinceTest !== null && <span className="ml-1">(vor {daysSinceTest} Tagen)</span>}
        </p>
        <Link
          to="/profile"
          className="inline-block text-xs font-semibold underline underline-offset-2 mt-2 opacity-90 hover:opacity-100 transition-opacity motion-reduce:transition-none"
        >
          Zum Schwellentest →
        </Link>
      </AlertDescription>
    </Alert>
  );
}
