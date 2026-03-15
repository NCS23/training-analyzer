/**
 * Utility functions for weekly plan date handling and formatting.
 */
import { CATEGORY_LABELS } from '@/constants/training';

export function categoryLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

/** Format a Date as YYYY-MM-DD using local timezone (not UTC). */
export function formatLocalDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function getMondayOfWeek(d: Date): string {
  const copy = new Date(d);
  const day = copy.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  copy.setDate(copy.getDate() + diff);
  return formatLocalDate(copy);
}

export function addWeeks(dateStr: string, weeks: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + weeks * 7);
  return formatLocalDate(d);
}

export function formatDateRange(weekStart: string): string {
  const start = new Date(weekStart);
  const end = new Date(weekStart);
  end.setDate(end.getDate() + 6);

  const startDay = start.getDate();
  const endDay = end.getDate();
  const startMonth = start.toLocaleDateString('de-DE', { month: 'short' });
  const endMonth = end.toLocaleDateString('de-DE', { month: 'short' });

  if (startMonth === endMonth) {
    return `${startDay}. – ${endDay}. ${startMonth}`;
  }
  return `${startDay}. ${startMonth} – ${endDay}. ${endMonth}`;
}
