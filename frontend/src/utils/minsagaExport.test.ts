// minsagaExport.test — Download-Wrapper für den Server-Export (#823).

import { afterEach, describe, expect, it, vi } from 'vitest';
import { downloadMinsagaExport } from './minsagaExport';
import { apiClient } from '@/api/client';

describe('downloadMinsagaExport (#823)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('holt den v2-Export, lädt ihn herunter und liefert die Zusammenfassung', async () => {
    const exportData = {
      version: 2,
      goals: [{}, {}],
      plans: [{}],
      weekly_plans: [{}, {}, {}],
    };
    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValue({ data: exportData });
    const createUrlSpy = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:test');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    const summary = await downloadMinsagaExport();

    expect(getSpy).toHaveBeenCalledWith('/api/v1/export/minsaga');
    expect(createUrlSpy).toHaveBeenCalledOnce();
    expect(clickSpy).toHaveBeenCalledOnce();
    expect(summary).toEqual({ goals: 2, plans: 1, weeks: 3 });
  });
});
