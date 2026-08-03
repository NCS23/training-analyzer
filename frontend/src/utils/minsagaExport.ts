// minsagaExport — Download des Server-Exports für die App-Migration (#823).
//
// Der Export wird komplett im Backend zusammengestellt (Format-Version 2,
// GET /api/v1/export/minsaga): Profil + Schwellentests, Ziele, Pläne mit
// Phasen UND Changelog (Entscheidungen samt Begründung) sowie alle
// gespeicherten Wochenplan-Wochen mit ihren Anpassungen. Workouts sind
// bewusst nicht enthalten — die kommen in minsaga aus Apple Health.

import { apiClient } from '@/api/client';

export interface MinsagaExportSummary {
  goals: number;
  plans: number;
  weeks: number;
}

/** Holt den Export vom Backend und löst den Browser-Download aus. */
export async function downloadMinsagaExport(): Promise<MinsagaExportSummary> {
  const response = await apiClient.get<{
    version: number;
    goals: unknown[];
    plans: unknown[];
    weekly_plans: unknown[];
  }>('/api/v1/export/minsaga');
  const exportData = response.data;

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'minsaga-export.json';
  anchor.click();
  window.URL.revokeObjectURL(url);

  return {
    goals: exportData.goals.length,
    plans: exportData.plans.length,
    weeks: exportData.weekly_plans.length,
  };
}
