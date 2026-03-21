import { useState, useEffect, useCallback } from 'react';
import { getLatestThresholdTest } from '@/api/threshold-tests';

/** Schwellentest gilt als veraltet nach 42 Tagen (6 Wochen). */
const REMINDER_THRESHOLD_DAYS = 42;

/** Dismiss-TTL: 7 Tage in Millisekunden. */
const DISMISS_TTL_MS = 7 * 24 * 60 * 60 * 1000;

const DISMISS_KEY = 'threshold-test-reminder-dismissed';

export type ReminderStatus = 'fresh' | 'due' | 'overdue' | 'never_tested';

export interface ThresholdReminderState {
  status: ReminderStatus;
  daysSinceTest: number | null;
  lastTestDate: string | null;
  loading: boolean;
  dismissed: boolean;
  dismiss: () => void;
}

function isDismissed(): boolean {
  const raw = localStorage.getItem(DISMISS_KEY);
  if (!raw) return false;
  const dismissedAt = parseInt(raw, 10);
  if (isNaN(dismissedAt)) return false;
  return Date.now() - dismissedAt < DISMISS_TTL_MS;
}

function calcDaysSince(dateStr: string): number {
  const testDate = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - testDate.getTime();
  return Math.floor(diffMs / (24 * 60 * 60 * 1000));
}

function calcStatus(daysSince: number): ReminderStatus {
  if (daysSince <= REMINDER_THRESHOLD_DAYS) return 'fresh';
  if (daysSince <= 56) return 'due'; // 6-8 Wochen
  return 'overdue'; // > 8 Wochen
}

export function useThresholdReminder(): ThresholdReminderState {
  const [status, setStatus] = useState<ReminderStatus>('fresh');
  const [daysSinceTest, setDaysSinceTest] = useState<number | null>(null);
  const [lastTestDate, setLastTestDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(isDismissed);

  useEffect(() => {
    loadReminderStatus();
  }, []);

  const loadReminderStatus = async () => {
    try {
      const test = await getLatestThresholdTest();
      const days = calcDaysSince(test.test_date);
      setDaysSinceTest(days);
      setLastTestDate(test.test_date);
      setStatus(calcStatus(days));
    } catch {
      // 404 = kein Test vorhanden
      setStatus('never_tested');
    } finally {
      setLoading(false);
    }
  };

  const dismiss = useCallback(() => {
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
    setDismissed(true);
  }, []);

  return { status, daysSinceTest, lastTestDate, loading, dismissed, dismiss };
}
